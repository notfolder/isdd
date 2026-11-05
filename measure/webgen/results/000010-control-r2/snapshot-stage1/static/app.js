(function () {
  "use strict";

  var SEGMENT_COLORS = ["#006400", "#00521a", "#003d14", "#1e6b2e", "#004d2a", "#2a7a3a"];
  var SPIN_MS = 5000;
  var NAME_KEY = "wof-player-name";

  var canvas = document.getElementById("wheel");
  var ctx = canvas.getContext("2d");
  var spinBtn = document.getElementById("spin-btn");
  var nameInput = document.getElementById("player-name");
  var resultEl = document.getElementById("result");
  var prizes = [];
  var rotation = 0;
  var spinning = false;

  // ---- helpers ----------------------------------------------------------
  function mod(x, m) {
    return ((x % m) + m) % m;
  }

  function api(url, options) {
    options = options || {};
    options.headers = { "Content-Type": "application/json" };
    return fetch(url, options).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          throw new Error(data.error || "Request failed (" + res.status + ")");
        }
        return data;
      });
    });
  }

  function savedName() {
    try { return localStorage.getItem(NAME_KEY) || ""; } catch (e) { return ""; }
  }

  function saveName(name) {
    try { localStorage.setItem(NAME_KEY, name); } catch (e) { /* ignore */ }
  }

  function setResult(text, isError) {
    resultEl.textContent = text;
    resultEl.classList.toggle("error", !!isError);
  }

  function formatDate(iso) {
    var d = new Date(iso);
    return isNaN(d.getTime()) ? iso : d.toLocaleString("en-US", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  }

  function truncate(text, max) {
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  // ---- wheel drawing ----------------------------------------------------
  function drawWheel() {
    var size = canvas.width;
    var c = size / 2;
    var r = c - 4;
    ctx.clearRect(0, 0, size, size);
    if (!prizes.length) {
      ctx.fillStyle = "#006400";
      ctx.beginPath();
      ctx.arc(c, c, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 22px Arial";
      ctx.textAlign = "center";
      ctx.fillText("No rewards yet", c, c);
      return;
    }
    var arc = (Math.PI * 2) / prizes.length;
    for (var i = 0; i < prizes.length; i++) {
      // Segment i starts at the top (12 o'clock) and runs clockwise.
      var start = i * arc - Math.PI / 2;
      var end = start + arc;
      ctx.beginPath();
      ctx.moveTo(c, c);
      ctx.arc(c, c, r, start, end);
      ctx.closePath();
      ctx.fillStyle = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#fffff0";
      ctx.stroke();

      ctx.save();
      ctx.translate(c, c);
      ctx.rotate(start + arc / 2);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 15px Arial";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(truncate(prizes[i].name, 22), r - 18, 0);
      ctx.restore();
    }
    // Hub in the centre.
    ctx.beginPath();
    ctx.arc(c, c, 30, 0, Math.PI * 2);
    ctx.fillStyle = "#003300";
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = "#fffff0";
    ctx.stroke();
  }

  // ---- spinning ---------------------------------------------------------
  // Shows (or clears) the validation message right under the name field.
  function showNameError(show) {
    var msg = document.getElementById("name-error");
    msg.hidden = !show;
    if (show) {
      nameInput.setAttribute("aria-invalid", "true");
    } else {
      nameInput.removeAttribute("aria-invalid");
    }
  }

  function finishSpin(prize, name) {
    spinning = false;
    spinBtn.disabled = false;
    setResult(name + " won: " + prize.name + (prize.description ? " — " + prize.description : ""));
  }

  function spin() {
    if (spinning) return;
    var name = nameInput.value.trim().replace(/\s+/g, " ");
    if (!name) {
      showNameError(true);
      setResult("Please enter your name before spinning.", true);
      nameInput.focus();
      return;
    }
    showNameError(false);
    if (!prizes.length) {
      setResult("No rewards are available right now.", true);
      return;
    }
    saveName(name);
    spinning = true;
    spinBtn.disabled = true;
    setResult("Spinning…");

    api("/api/spin", { method: "POST", body: JSON.stringify({ name: name }) })
      .then(function (data) {
        var index = -1;
        for (var i = 0; i < prizes.length; i++) {
          if (prizes[i].id === data.prize.id) { index = i; break; }
        }
        if (index < 0) {
          // Prize list changed on the server; reload it and retry the display.
          return loadPrizes().then(function () { return data; });
        }
        return data;
      })
      .then(function (data) {
        var n = prizes.length;
        var index = -1;
        for (var i = 0; i < n; i++) {
          if (prizes[i].id === data.prize.id) { index = i; break; }
        }
        var segment = 360 / n;
        var centre = (index + 0.5) * segment;
        // Land somewhere inside the winning segment, not exactly on the edge.
        var jitter = (Math.random() - 0.5) * segment * 0.6;
        var base = rotation + 6 * 360; // at least six full turns
        var target = base + mod(-centre + jitter - base, 360);
        canvas.style.transition = "transform " + SPIN_MS + "ms cubic-bezier(0.17, 0.67, 0.12, 0.99)";
        canvas.style.transform = "rotate(" + target + "deg)";
        rotation = target;
        window.setTimeout(function () {
          finishSpin(data.prize, name);
          loadMyRecordsIfOpen(name);
        }, SPIN_MS + 100);
      })
      .catch(function (err) {
        spinning = false;
        spinBtn.disabled = false;
        setResult(err.message, true);
      });
  }

  // ---- prizes -----------------------------------------------------------
  function loadPrizes() {
    return api("/api/prizes").then(function (data) {
      prizes = data.prizes;
      drawWheel();
      renderPrizeTable();
    });
  }

  function renderPrizeTable() {
    var body = document.getElementById("reward-body");
    var status = document.getElementById("reward-status");
    body.textContent = "";
    if (!prizes.length) {
      status.textContent = "No rewards have been added yet.";
      return;
    }
    status.textContent = prizes.length + " rewards on the wheel.";
    prizes.forEach(function (p) {
      var tr = document.createElement("tr");
      var nameTd = document.createElement("td");
      nameTd.className = "prize-name";
      nameTd.textContent = p.name;
      var descTd = document.createElement("td");
      descTd.textContent = p.description;
      var chanceTd = document.createElement("td");
      chanceTd.className = "num";
      chanceTd.textContent = p.chance.toFixed(1) + "%";
      tr.appendChild(nameTd);
      tr.appendChild(descTd);
      tr.appendChild(chanceTd);
      body.appendChild(tr);
    });
  }

  // ---- records ----------------------------------------------------------
  function loadRecords(name) {
    var body = document.getElementById("records-body");
    var summary = document.getElementById("records-summary");
    if (!name) {
      body.textContent = "";
      summary.textContent = "Enter your name above and press “Show my records”.";
      return;
    }
    summary.textContent = "Loading…";
    api("/api/records?name=" + encodeURIComponent(name))
      .then(function (data) {
        body.textContent = "";
        if (!data.records.length) {
          summary.textContent = "No winning records yet for “" + data.name + "”. Go spin the wheel!";
          return;
        }
        summary.textContent = data.name + " has " + data.total + " recorded spin" +
          (data.total === 1 ? "" : "s") + (data.records.length < data.total
            ? " (showing the latest " + data.records.length + ")" : "") + ".";
        data.records.forEach(function (rec) {
          var tr = document.createElement("tr");
          var playerTd = document.createElement("td");
          playerTd.textContent = rec.user_name;
          var prizeTd = document.createElement("td");
          prizeTd.className = "prize-name";
          prizeTd.textContent = rec.prize_name;
          var dateTd = document.createElement("td");
          dateTd.textContent = formatDate(rec.created_at);
          tr.appendChild(playerTd);
          tr.appendChild(prizeTd);
          tr.appendChild(dateTd);
          body.appendChild(tr);
        });
      })
      .catch(function (err) {
        body.textContent = "";
        summary.textContent = err.message;
      });
  }

  function loadMyRecordsIfOpen(name) {
    if (currentView() === "records") {
      var input = document.getElementById("records-name");
      input.value = name;
      loadRecords(name);
    }
  }

  // ---- routing ----------------------------------------------------------
  var VIEWS = ["wheel", "rewards", "records"];

  function currentView() {
    var v = (window.location.hash || "").replace(/^#\/?/, "");
    if (v === "prizes") v = "rewards"; // old link
    return VIEWS.indexOf(v) >= 0 ? v : "wheel";
  }

  function showView() {
    var view = currentView();
    VIEWS.forEach(function (v) {
      document.getElementById("view-" + v).hidden = v !== view;
    });
    document.querySelectorAll(".main-nav a").forEach(function (a) {
      if (a.getAttribute("data-nav") === view) {
        a.setAttribute("aria-current", "page");
      } else {
        a.removeAttribute("aria-current");
      }
    });
    if (view === "records") {
      var input = document.getElementById("records-name");
      if (!input.value) input.value = savedName();
      loadRecords(input.value.trim());
    }
    if (view === "rewards") {
      loadPrizes().catch(function (err) {
        document.getElementById("reward-status").textContent = err.message;
      });
    }
    window.scrollTo(0, 0);
  }

  // ---- init -------------------------------------------------------------
  spinBtn.addEventListener("click", spin);
  nameInput.addEventListener("input", function () {
    if (nameInput.value.trim()) showNameError(false);
  });
  nameInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") spin();
  });
  document.getElementById("records-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var name = document.getElementById("records-name").value.trim();
    if (name) saveName(name);
    loadRecords(name);
  });
  window.addEventListener("hashchange", showView);

  nameInput.value = savedName();
  if (!window.location.hash) {
    window.location.hash = "#/wheel";
  }
  loadPrizes()
    .catch(function (err) { setResult("Could not load rewards: " + err.message, true); })
    .then(showView);
})();
