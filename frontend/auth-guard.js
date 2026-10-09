(() => {
  const API_BASE = "http://127.0.0.1:8001";
  const token = localStorage.getItem("criAccessToken");

  if (!token) {
    const next = encodeURIComponent(
      location.pathname.split("/").pop() || "index.html"
    );
    location.replace(`auth.html?next=${next}`);
    return;
  }

  const originalFetch = window.fetch.bind(window);

  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : input.url;
    const isApiRequest = url && url.startsWith(API_BASE + "/");

    if (isApiRequest && !url.includes("/auth/")) {
      const headers = new Headers(
        init?.headers ||
        (input instanceof Request ? input.headers : undefined)
      );

      headers.set(
        "Authorization",
        `Bearer ${localStorage.getItem("criAccessToken") || ""}`
      );

      init = Object.assign({}, init || {}, { headers });
    }

    const response = await originalFetch(input, init);

    if (response.status === 401 && isApiRequest) {
      localStorage.removeItem("criAccessToken");
      localStorage.removeItem("criUser");
      location.replace("auth.html");
    }

    return response;
  };

  document.addEventListener("DOMContentLoaded", function () {
    let user = {};
    try {
      user = JSON.parse(localStorage.getItem("criUser") || "{}");
    } catch (_) {
      user = {};
    }

    const host = document.querySelector(".topbar-actions");

    if (host && !document.getElementById("authAccountMenu")) {
      const wrap = document.createElement("div");
      wrap.id = "authAccountMenu";
      wrap.style.cssText =
        "display:flex;align-items:center;gap:10px;margin-left:10px";

      const label = document.createElement("span");
      label.textContent = user.name || user.email || "Account";
      label.style.cssText =
        "font-size:12px;opacity:.8;max-width:150px;overflow:hidden;text-overflow:ellipsis";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "secondary-button";
      btn.textContent = "Sign out";

      btn.addEventListener("click", () => {
        localStorage.removeItem("criAccessToken");
        localStorage.removeItem("criUser");
        location.replace("auth.html");
      });

      wrap.append(label, btn);
      host.appendChild(wrap);
    }
  });
})();