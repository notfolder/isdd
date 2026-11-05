// Shared helpers for all pages.
(function () {
  const PLAYER_KEY = "wof-player";

  window.WOF = {
    getPlayer() {
      try {
        return (localStorage.getItem(PLAYER_KEY) || "").trim();
      } catch (e) {
        return "";
      }
    },
    setPlayer(name) {
      try {
        localStorage.setItem(PLAYER_KEY, name);
      } catch (e) {
        /* storage unavailable: ignore */
      }
    },
    // Build an element with text content (never innerHTML for user data).
    el(tag, attrs, children) {
      const node = document.createElement(tag);
      if (attrs) {
        for (const [k, v] of Object.entries(attrs)) {
          if (k === "class") node.className = v;
          else if (k === "text") node.textContent = v;
          else node.setAttribute(k, v);
        }
      }
      (children || []).forEach((c) => {
        if (c == null) return;
        node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
      });
      return node;
    },
    formatDate(iso) {
      const d = new Date(iso);
      return isNaN(d) ? iso : d.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });
    },
    async api(url, options) {
      const res = await fetch(url, options);
      let data = {};
      try {
        data = await res.json();
      } catch (e) {
        /* non-JSON body */
      }
      if (!res.ok) throw new Error(data.error || "Request failed (" + res.status + ")");
      return data;
    },
  };
})();
