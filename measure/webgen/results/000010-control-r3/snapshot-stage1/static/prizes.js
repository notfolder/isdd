(function () {
  const container = document.getElementById("prizes-container");

  function render(prizes) {
    container.replaceChildren();
    if (prizes.length === 0) {
      container.appendChild(WOF.el("p", { class: "empty", text: "No prizes have been set up yet." }));
      return;
    }
    const total = prizes.reduce((sum, p) => sum + p.weight, 0) || 1;

    const headRow = WOF.el("tr", null, [
      WOF.el("th", { text: "#" }),
      WOF.el("th", { text: "Prize" }),
      WOF.el("th", { text: "Description" }),
      WOF.el("th", { text: "Result" }),
      WOF.el("th", { class: "num", text: "Chance" }),
    ]);

    const rows = prizes.map((p, i) =>
      WOF.el("tr", null, [
        WOF.el("td", { text: String(i + 1) }),
        WOF.el("td", { text: p.name }),
        WOF.el("td", { text: p.description }),
        WOF.el("td", null, [
          WOF.el("span", { class: p.is_win ? "badge" : "badge none", text: p.is_win ? "Win" : "No prize" }),
        ]),
        WOF.el("td", { class: "num", text: ((p.weight / total) * 100).toFixed(1) + "%" }),
      ])
    );

    const table = WOF.el("table", { "aria-label": "Prize list" }, [
      WOF.el("thead", null, [headRow]),
      WOF.el("tbody", null, rows),
    ]);
    container.appendChild(table);
  }

  WOF.api("/api/prizes")
    .then((data) => render(data.prizes))
    .catch((err) => {
      container.replaceChildren(WOF.el("p", { class: "empty", text: "Could not load prizes: " + err.message }));
    });
})();
