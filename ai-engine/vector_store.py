import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "contract_clauses"


class VectorStore:
    """
    Stores contract clause embeddings in ChromaDB
    and retrieves semantically similar clauses.
    """

    def __init__(self):
        print("Initializing ChromaDB...")

        self.client = chromadb.PersistentClient(
            path="chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME
        )

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        print("Vector store initialized successfully.")

    def add_clauses(self, clauses):
        """
        Add contract clauses to ChromaDB.

        Expected clause:

        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": "..."
        }
        """

        if not clauses:
            return

        documents = []
        ids = []
        metadatas = []

        for clause in clauses:

            section = str(
                clause.get("section", "")
            )

            clause_id = (
                f"section_{section}"
            )

            documents.append(
                clause.get("text", "")
            )

            ids.append(clause_id)

            metadatas.append(
                {
                    "section": section,
                    "clause_type": str(
                        clause.get(
                            "clause_type",
                            "Other"
                        )
                    ),
                    "page": int(
                        clause.get("page", 0)
                    )
                }
            )

        embeddings = self.model.encode(
            documents
        ).tolist()

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(
            f"Stored {len(documents)} clauses in ChromaDB."
        )

    def search(self, query, top_k=3):
        """
        Search ChromaDB using semantic similarity.
        """

        query_embedding = self.model.encode(
            query
        ).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        return results


if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("CHROMADB VECTOR STORE TEST")
    print("=" * 60)

    store = VectorStore()

    test_clauses = [
        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": (
                "The Customer shall pay the Supplier "
                "within 30 days of receiving an invoice."
            )
        },
        {
            "section": "2",
            "clause_type": "Termination",
            "page": 2,
            "text": (
                "Either party may terminate this agreement "
                "by providing 30 days written notice."
            )
        }
    ]

    # Store clauses
    store.add_clauses(
        test_clauses
    )

    # Search
    query = (
        "What does the contract say about "
        "termination notice?"
    )

    results = store.search(
        query,
        top_k=2
    )

    print("\nSearch query:")
    print(query)

    print("\nSearch results:")

    for i, document in enumerate(
        results["documents"][0],
        start=1
    ):

        metadata = results["metadatas"][0][i - 1]

        distance = results["distances"][0][i - 1]

        print("\n" + "-" * 50)

        print(
            f"Result: {i}"
        )

        print(
            f"Section: {metadata['section']}"
        )

        print(
            f"Type: {metadata['clause_type']}"
        )

        print(
            f"Page: {metadata['page']}"
        )

        print(
            f"Distance: {round(distance, 4)}"
        )

        print(
            f"Text: {document}"
        )