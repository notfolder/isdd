(() => {
  "use strict";

  const NAME_KEY = "wheelPlayerName";
  const SPIN_MS = 4000;
  const VIEWS = ["spin", "prizes", "records", "manage"];
  const SEGMENT_COLORS = ["#006400", "#1b5e20", "#004d00", "#2e7d32"];
  const SERVER_ERROR = "Something went wrong. Please try again.";

  const $ = (id) => document.getElementById(id);
  let prizes = [];
  let wheelRotation = 0;
  let spinning = false;

  // 画面を切り替え、開いた画面のために景品の一覧を読み直して表とホイールを描く
  function showViewAndReload(name) {
    const view = VIEWS.includes(name) ? name : "spin";
    for (const other of VIEWS) {
      $("view-" + other).hidden = other !== view;
    }
    for (const link of document.querySelectorAll("nav a[data-view]")) {
      if (link.dataset.view === view) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    }
    fetch("/api/prizes")
      .then((response) => response.json())
      .then((data) => {
        prizes = data.prizes || [];
        const body = $("prizes-body");
        body.textContent = "";
        $("prizes-empty").hidden = prizes.length > 0;
        for (const prize of prizes) {
          const row = document.createElement("tr");
          const nameCell = document.createElement("td");
          nameCell.textContent = prize.name;
          const descriptionCell = document.createElement("td");
          descriptionCell.textContent = prize.description;
          row.append(nameCell, descriptionCell);
          body.appendChild(row);
        }
        renderManagePrizes(prizes);
        if (!spinning) {
          renderWheel(prizes);
        }
      })
      .catch(() => {
        $("spin-error").textContent = SERVER_ERROR;
      });
  }

  // 景品の管理の表を描く。各行に Remove を付ける
  function renderManagePrizes(list) {
    const body = $("manage-body");
    body.textContent = "";
    $("manage-empty").hidden = list.length > 0;
    for (const prize of list) {
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      nameCell.textContent = prize.name;
      const descriptionCell = document.createElement("td");
      descriptionCell.textContent = prize.description;
      const actionCell = document.createElement("td");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Remove";
      remove.addEventListener("click", () => {
        $("manage-error").textContent = "";
        fetch("/api/prizes/" + encodeURIComponent(prize.id), { method: "DELETE" })
          .then(async (response) => {
            if (!response.ok) {
              const data = await response.json().catch(() => ({}));
              throw new Error(data.error || SERVER_ERROR);
            }
          })
          .then(() => showViewAndReload("manage"))
          .catch((failure) => {
            $("manage-error").textContent = failure.message;
          });
      });
      actionCell.appendChild(remove);
      row.append(nameCell, descriptionCell, actionCell);
      body.appendChild(row);
    }
  }

  function renderWheel(list) {
    const wheel = $("wheel");
    wheel.textContent = "";
    if (list.length === 0) {
      return;
    }
    const size = 300;
    const center = size / 2;
    const radius = size / 2 - 2;
    const angle = 360 / list.length;
    const svgNs = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNs, "svg");
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    svg.setAttribute("width", size);
    svg.setAttribute("height", size);
    list.forEach((prize, index) => {
      const start = (index * angle - 90) * Math.PI / 180;
      const end = ((index + 1) * angle - 90) * Math.PI / 180;
      const large = angle > 180 ? 1 : 0;
      const path = document.createElementNS(svgNs, "path");
      const d = [
        `M ${center} ${center}`,
        `L ${center + radius * Math.cos(start)} ${center + radius * Math.sin(start)}`,
        `A ${radius} ${radius} 0 ${large} 1 ${center + radius * Math.cos(end)} ${center + radius * Math.sin(end)}`,
        "Z",
      ].join(" ");
      path.setAttribute("d", d);
      path.setAttribute("fill", SEGMENT_COLORS[index % SEGMENT_COLORS.length]);
      path.setAttribute("stroke", "#f5f5f5");
      path.setAttribute("stroke-width", "1");
      svg.appendChild(path);
      const mid = (index + 0.5) * angle;
      const tx = center + radius * 0.62 * Math.cos((mid - 90) * Math.PI / 180);
      const ty = center + radius * 0.62 * Math.sin((mid - 90) * Math.PI / 180);
      const text = document.createElementNS(svgNs, "text");
      text.setAttribute("x", tx);
      text.setAttribute("y", ty);
      text.setAttribute("fill", "#ffffff");
      text.setAttribute("font-size", "13");
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("dominant-baseline", "middle");
      text.setAttribute("transform", `rotate(${mid} ${tx} ${ty})`);
      text.textContent = prize.name;
      svg.appendChild(text);
    });
    wheel.appendChild(svg);
  }

  function rememberPlayerName(name) {
    try {
      localStorage.setItem(NAME_KEY, name);
    } catch (error) {
      // 保存できなくても画面の操作は続けられる
    }
    return name;
  }

  // 保存された利用者名を両方の入力欄の初期値にする
  let savedName = "";
  try {
    savedName = localStorage.getItem(NAME_KEY) || "";
  } catch (error) {
    savedName = "";
  }
  $("spin-name").value = savedName;
  $("records-name").value = savedName;

  // 抽選: 結果の位置へホイールを回し、回り終えてから結果を出す
  $("spin-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (spinning) {
      return;
    }
    const error = $("spin-error");
    const result = $("spin-result");
    error.textContent = "";
    result.textContent = "";
    const name = $("spin-name").value.trim();
    if (name.length === 0 || name.length > 30) {
      error.textContent = "Please enter your name (1–30 characters).";
      return;
    }
    rememberPlayerName(name);
    const button = $("spin-button");
    spinning = true;
    button.disabled = true;
    fetch("/api/spin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_name: name }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || SERVER_ERROR);
        }
        return data;
      })
      .then((data) => {
        const angle = 360 / prizes.length;
        const target = (360 - (((data.index + 0.5) * angle) % 360)) % 360;
        wheelRotation = wheelRotation - (wheelRotation % 360) + 5 * 360 + target;
        $("wheel").style.transform = `rotate(${wheelRotation}deg)`;
        return new Promise((resolve) => setTimeout(resolve, SPIN_MS)).then(() => data);
      })
      .then((data) => {
        result.textContent = `You won: ${data.prize.name}`;
        $("records-name").value = name;
      })
      .catch((failure) => {
        error.textContent = failure.message;
      })
      .finally(() => {
        spinning = false;
        button.disabled = false;
      });
  });

  // 景品の追加: 名前を送り、成功したら入力欄を空にして一覧を読み直す
  $("manage-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const error = $("manage-error");
    error.textContent = "";
    const name = $("manage-name").value.trim();
    fetch("/api/prizes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name }),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || SERVER_ERROR);
        }
        return data;
      })
      .then(() => {
        $("manage-name").value = "";
        showViewAndReload("manage");
      })
      .catch((failure) => {
        error.textContent = failure.message;
      });
  });

  // 抽選記録の表を描く。各行は利用者名・景品名・抽選日時
  function renderRecords(records) {
    const body = $("records-body");
    body.textContent = "";
    $("records-empty").hidden = records.length > 0;
    for (const record of records) {
      const row = document.createElement("tr");
      const playerCell = document.createElement("td");
      playerCell.textContent = record.player_name;
      const prizeCell = document.createElement("td");
      prizeCell.textContent = record.prize_name;
      const timeCell = document.createElement("td");
      timeCell.textContent = new Date(record.spun_at).toLocaleString("en-US");
      row.append(playerCell, prizeCell, timeCell);
      body.appendChild(row);
    }
  }

  // 抽選記録の一括削除: 確認ダイアログで OK のときだけ DELETE /api/records を送る
  function clearRecords() {
    const error = $("records-error");
    const status = $("records-status");
    error.textContent = "";
    status.textContent = "";
    if (!window.confirm("Delete all winning records? This cannot be undone.")) {
      return;
    }
    fetch("/api/records", { method: "DELETE" })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || SERVER_ERROR);
        }
        return data;
      })
      .then(() => {
        renderRecords([]);
        status.textContent = "All winning records were deleted.";
      })
      .catch((failure) => {
        error.textContent = failure.message;
      });
  }
  $("clear-records-button").addEventListener("click", clearRecords);

  // 自分の記録: 利用者名の完全一致で抽選記録を新しい順に出す
  $("records-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const error = $("records-error");
    const body = $("records-body");
    error.textContent = "";
    const name = $("records-name").value.trim();
    if (name.length === 0) {
      error.textContent = "Please enter your name";
      body.textContent = "";
      $("records-empty").hidden = true;
      return;
    }
    rememberPlayerName(name);
    fetch("/api/records?player_name=" + encodeURIComponent(name))
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Please enter your name");
        }
        return data;
      })
      .then((data) => {
        $("records-status").textContent = "";
        renderRecords(data.records);
      })
      .catch((failure) => {
        error.textContent = failure.message;
      });
  });

  // 画面の切り替え（#/spin、#/prizes、#/records、#/manage）
  window.addEventListener("hashchange", () => showViewAndReload(location.hash.replace(/^#\//, "")));
  showViewAndReload(location.hash.replace(/^#\//, ""));
})();
