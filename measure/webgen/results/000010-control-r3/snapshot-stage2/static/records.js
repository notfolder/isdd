(function () {
  const form = document.getElementById("lookup-form");
  const nameInput = document.getElementById("lookup-name");
  const summary = document.getElementById("summary");
  const winsBox = document.getElementById("wins");
  const recentBox = document.getElementById("recent");

  // Every winning record shows the date, the player's name and the prize.
  function renderWinsTable(box, rows, label) {
    box.replaceChildren();
    if (rows.length === 0) {
      box.appendChild(WOF.el("p", { class: "empty", text: "No winning records yet." }));
      return;
    }
    const head = ["Date", "Player", "Prize"];
    const headRow = WOF.el("tr", null, head.map((h) => WOF.el("th", { text: h })));
    const body = rows.map((r) =>
      WOF.el("tr", null, [
        WOF.el("td", { text: WOF.formatDate(r.created_at) }),
        WOF.el("td", { text: r.player }),
        WOF.el("td", { text: r.prize_name }),
      ])
    );
    box.appendChild(
      WOF.el("table", { "aria-label": label }, [
        WOF.el("thead", null, [headRow]),
        WOF.el("tbody", null, body),
      ])
    );
  }

  function renderSummary(player, spins) {
    const wins = spins.filter((s) => s.is_win).length;
    summary.replaceChildren(
      WOF.el("div", { class: "stats" }, [
        WOF.el("div", { class: "stat" }, [
          WOF.el("div", { class: "value", text: String(spins.length) }),
          WOF.el("div", { class: "label", text: "Total spins" }),
        ]),
        WOF.el("div", { class: "stat" }, [
          WOF.el("div", { class: "value", text: String(wins) }),
          WOF.el("div", { class: "label", text: "Prizes won" }),
        ]),
      ]),
      WOF.el("p", { class: "lead", text: "Showing records for " + player + "." })
    );
  }

  async function loadRecords(player) {
    winsBox.replaceChildren(WOF.el("p", { class: "empty", text: "Loading..." }));
    try {
      const data = await WOF.api("/api/spins?player=" + encodeURIComponent(player));
      renderSummary(data.player, data.spins);
      renderWinsTable(
        winsBox,
        data.spins.filter((s) => s.is_win),
        "My wins"
      );
    } catch (err) {
      summary.replaceChildren();
      winsBox.replaceChildren(WOF.el("p", { class: "empty", text: err.message }));
    }
  }

  async function loadRecent() {
    try {
      const data = await WOF.api("/api/winners");
      renderWinsTable(recentBox, data.winners, "Recent winners");
    } catch (err) {
      recentBox.replaceChildren(WOF.el("p", { class: "empty", text: err.message }));
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const player = nameInput.value.trim();
    if (!player) {
      nameInput.focus();
      return;
    }
    WOF.setPlayer(player);
    loadRecords(player);
  });

  const saved = WOF.getPlayer();
  if (saved) {
    nameInput.value = saved;
    loadRecords(saved);
  }
  loadRecent();
})();
