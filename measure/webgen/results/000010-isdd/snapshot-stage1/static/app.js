(() => {
  "use strict";

  const NAME_KEY = "wheelPlayerName";
  const SPIN_MS = 4000;
  const VIEWS = ["spin", "prizes", "records"];
  const SEGMENT_COLORS = ["#8b0000", "#b22222", "#6e0000", "#a52a2a"];

  const $ = (id) => document.getElementById(id);
  let prizes = [];
  let wheelRotation = 0;
  let spinning = false;

  function showView(name) {
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
  }

  function rememberPlayerName(name) {
    try {
      localStorage.setItem(NAME_KEY, name);
    } catch (error) {
      // 保存できなくても画面の操作は続けられる
    }
    return name;
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

  // 保存された利用者名を両方の入力欄の初期値にする
  let savedName = "";
  try {
    savedName = localStorage.getItem(NAME_KEY) || "";
  } catch (error) {
    savedName = "";
  }
  $("spin-name").value = savedName;
  $("records-name").value = savedName;

  // 景品の一覧を読み、表とホイールを描く
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
      renderWheel(prizes);
    })
    .catch(() => {
      $("spin-error").textContent = "Something went wrong. Please try again.";
    });

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
          throw new Error(data.error || "Something went wrong. Please try again.");
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
        body.textContent = "";
        $("records-empty").hidden = data.records.length > 0;
        for (const record of data.records) {
          const row = document.createElement("tr");
          const timeCell = document.createElement("td");
          timeCell.textContent = new Date(record.spun_at).toLocaleString("en-US");
          const prizeCell = document.createElement("td");
          prizeCell.textContent = record.prize_name;
          row.append(timeCell, prizeCell);
          body.appendChild(row);
        }
      })
      .catch((failure) => {
        error.textContent = failure.message;
      });
  });

  // 画面の切り替え（#/spin、#/prizes、#/records）
  window.addEventListener("hashchange", () => showView(location.hash.replace(/^#\//, "")));
  showView(location.hash.replace(/^#\//, ""));
})();
