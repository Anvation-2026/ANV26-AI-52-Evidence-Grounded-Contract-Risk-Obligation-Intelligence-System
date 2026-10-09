import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers.auth import router as auth_router
from app.services.auth_service import decode_token

from app.database.connection import engine, Base, SessionLocal
from app.models import Contract, Clause, AuditEvent, ReviewAction
from app.routers.contracts import router as contracts_router


app = FastAPI(
    title="Contract Risk Intelligence API",
    description="Evidence-grounded contract risk and obligation analysis system",
    version="1.0.0"
)


# Create tables if they don't already exist, then add the ownership column to
# databases created by older MVP versions. Legacy rows remain unowned and are
# intentionally inaccessible until an administrator explicitly migrates them.
Base.metadata.create_all(bind=engine)
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "contracts" in inspector.get_table_names():
        contract_columns = {column["name"] for column in inspector.get_columns("contracts")}
        if "owner_id" not in contract_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE contracts ADD COLUMN owner_id INTEGER NULL"))
            try:
                with engine.begin() as connection:
                    connection.execute(text("CREATE INDEX ix_contracts_owner_id ON contracts (owner_id)"))
            except Exception:
                pass  # Index may already exist on some migrated databases.
except Exception as migration_error:
    # Fail loudly: silently starting without tenant isolation is unsafe.
    raise RuntimeError(f"Database ownership migration failed: {migration_error}") from migration_error


# Allow frontend to communicate with backend
import os

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5501,http://localhost:5501,"
            "http://127.0.0.1:5500,http://localhost:5500"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Contract routes
app.include_router(auth_router)
app.include_router(contracts_router)


@app.middleware("http")
async def require_authentication(request, call_next):
    # Health and sign-in remain public. Workspace APIs require a valid token.
    path = request.url.path
    public = path == "/health" or path.startswith("/auth/") or path in {"/openapi.json", "/docs", "/redoc"}
    if request.method == "OPTIONS" or public:
        return await call_next(request)
    if path.startswith("/contracts") or path.startswith("/audit"):
        auth = request.headers.get("authorization", "")
        scheme, _, token = auth.partition(" ")
        payload = decode_token(token) if scheme.lower() == "bearer" else None
        if not payload:
            return JSONResponse(status_code=401, content={"detail": "Sign in to access contract workspace."})
        request.state.user = payload

        # Enforce tenant isolation centrally for every route with a contract ID.
        # This also protects endpoints that are easy to overlook when adding new features.
        match = re.match(r"^/contracts/(\d+)(?:/|$)", path)
        if match:
            contract_id = int(match.group(1))
            db = SessionLocal()
            try:
                contract = db.query(Contract).filter(Contract.id == contract_id).first()
                if not contract or contract.owner_id is None or int(contract.owner_id) != int(payload["sub"]):
                    return JSONResponse(status_code=404, content={"detail": "Contract not found."})
                # A version comparison can reference a second contract through a query parameter.
                other_id = request.query_params.get("v2_contract_id")
                if other_id and other_id.isdigit():
                    other = db.query(Contract).filter(Contract.id == int(other_id)).first()
                    if not other or other.owner_id is None or int(other.owner_id) != int(payload["sub"]):
                        return JSONResponse(status_code=404, content={"detail": "Compared contract not found."})
            finally:
                db.close()
    return await call_next(request)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "contract-risk-intelligence-backend"
    }
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)