// Front end for the wheel of fortune. Plain JavaScript, no build step.
(function () {
  "use strict";

  var MAX_NAME_LENGTH = 30;
  var SPIN_DURATION_MS = 4000;
  var EXTRA_TURNS = 5;
  var SLICE_COLORS = ["#8B0000", "#5C0A0F", "#A61B1B", "#6E0D12"];
  var TWO_PI = Math.PI * 2;

  var pageRenderers = {
    "spin": renderSpinPage,
    "prizes": renderPrizesPage,
    "my-winnings": renderMyWinningsPage
  };

  function $(id) { return document.getElementById(id); }

  function setText(el, text) { el.textContent = text; }

  // Show the navigation highlight for the page in use.
  function renderNavigation(current) {
    var links = document.querySelectorAll(".site-nav a");
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute("data-page") === current) {
        links[i].setAttribute("aria-current", "page");
      } else {
        links[i].removeAttribute("aria-current");
      }
    }
  }

  function currentPage() {
    var name = window.location.hash.replace(/^#\/?/, "");
    return pageRenderers.hasOwnProperty(name) ? name : "spin";
  }

  function route() {
    var page = currentPage();
    renderNavigation(page);
    var app = $("app");
    app.innerHTML = "";
    pageRenderers[page](app);
  }

  function requestJson(method, url, body) {
    var options = { method: method, headers: {}, credentials: "same-origin" };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    return fetch(url, options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        return { ok: response.ok, status: response.status, data: data };
      });
    });
  }

  // Draw the wheel: slice i starts at the top and runs clockwise.
  function drawWheel(canvas, prizes, rotation) {
    var ctx = canvas.getContext("2d");
    var size = canvas.width;
    var center = size / 2;
    var radius = center - 6;
    var count = prizes.length;
    var slice = TWO_PI / count;
    ctx.clearRect(0, 0, size, size);
    for (var i = 0; i < count; i++) {
      var start = -Math.PI / 2 + i * slice + rotation;
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.arc(center, center, radius, start, start + slice);
      ctx.closePath();
      ctx.fillStyle = SLICE_COLORS[i % SLICE_COLORS.length];
      ctx.fill();
      ctx.strokeStyle = "#FFFFFF";
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.save();
      ctx.translate(center, center);
      ctx.rotate(start + slice / 2);
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 16px system-ui, Arial, sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(prizes[i].name, radius - 16, 0);
      ctx.restore();
    }
    ctx.beginPath();
    ctx.arc(center, center, 24, 0, TWO_PI);
    ctx.fillStyle = "#FFFFFF";
    ctx.fill();
    ctx.strokeStyle = "#8B0000";
    ctx.lineWidth = 4;
    ctx.stroke();
  }

  // Rotation after EXTRA_TURNS full turns that brings slice `index` under the top pointer.
  function targetRotation(index, count, current) {
    var slice = TWO_PI / count;
    var want = mod(-(index + 0.5) * slice, TWO_PI);
    var now = mod(current, TWO_PI);
    var delta = mod(want - now, TWO_PI);
    return current + EXTRA_TURNS * TWO_PI + delta;
  }

  function mod(value, base) { return ((value % base) + base) % base; }

  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  // Animate the wheel from `from` to `to` and call done() at the end.
  function spinWheelTo(canvas, prizes, from, to, done) {
    var began = null;
    function frame(now) {
      if (began === null) { began = now; }
      var t = Math.min(1, (now - began) / SPIN_DURATION_MS);
      var rotation = from + (to - from) * easeOutCubic(t);
      drawWheel(canvas, prizes, rotation);
      if (t < 1) {
        window.requestAnimationFrame(frame);
      } else if (done) {
        done();
      }
    }
    window.requestAnimationFrame(frame);
  }

  function renderSpinPage(app) {
    var panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML =
      '<h2>Spin the wheel</h2>' +
      '<div class="spin-layout">' +
      '  <div class="wheel-wrap"><div class="pointer" aria-hidden="true"></div>' +
      '    <canvas id="wheel" width="420" height="420" role="img" aria-label="Prize wheel"></canvas></div>' +
      '  <form class="spin-form" id="spin-form" novalidate>' +
      '    <label for="display-name">Your name (optional)</label>' +
      '    <input type="text" id="display-name" name="display_name" placeholder="Guest" autocomplete="off">' +
      '    <p class="field-error" id="name-error" role="alert"></p>' +
      '    <button type="submit" id="spin-button">Spin</button>' +
      '    <p class="result" id="result" aria-live="polite"></p>' +
      '    <p class="result-note" id="result-note"></p>' +
      '  </form>' +
      '</div>';
    app.appendChild(panel);

    var canvas = $("wheel");
    var form = $("spin-form");
    var button = $("spin-button");
    var input = $("display-name");
    var nameError = $("name-error");
    var result = $("result");
    var note = $("result-note");
    var prizes = [];
    var rotation = 0;
    var spinning = false;

    requestJson("GET", "/api/prizes").then(function (res) {
      if (!res.ok || !res.data.length) {
        setText(result, "No prizes are available yet.");
        button.disabled = true;
        return;
      }
      prizes = res.data;
      drawWheel(canvas, prizes, rotation);
    }).catch(function () {
      setText(result, "Something went wrong. Please try again.");
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (spinning || !prizes.length) { return; }
      var name = input.value.trim();
      setText(nameError, "");
      if (name.length > MAX_NAME_LENGTH) {
        setText(nameError, "Name must be 30 characters or less.");
        return;
      }
      spinning = true;
      button.disabled = true;
      setText(result, "Spinning...");
      setText(note, "");
      requestJson("POST", "/api/spin", { display_name: name }).then(function (res) {
        if (!res.ok) {
          spinning = false;
          button.disabled = false;
          setText(result, "");
          setText(nameError, res.data.error || "Something went wrong. Please try again.");
          return;
        }
        var index = -1;
        for (var i = 0; i < prizes.length; i++) {
          if (prizes[i].id === res.data.prize.id) { index = i; break; }
        }
        var target = targetRotation(index, prizes.length, rotation);
        spinWheelTo(canvas, prizes, rotation, target, function () {
          rotation = target;
          spinning = false;
          button.disabled = false;
          if (res.data.recorded) {
            setText(result, "You won: " + res.data.prize.name + "!");
            note.innerHTML = '';
            var link = document.createElement("a");
            link.href = "#/my-winnings";
            link.className = "button";
            link.textContent = "See My Winnings";
            note.appendChild(link);
          } else {
            setText(result, "No prize this time");
            setText(note, "Try again!");
          }
        });
      }).catch(function () {
        spinning = false;
        button.disabled = false;
        setText(result, "Something went wrong. Please try again.");
      });
    });
  }

  function renderPrizesPage(app) {
    var panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML = "<h2>Prizes</h2><p class=\"notice\">Loading...</p>";
    app.appendChild(panel);
    requestJson("GET", "/api/prizes").then(function (res) {
      panel.innerHTML = "<h2>Prizes</h2>";
      if (!res.ok || !res.data.length) {
        panel.insertAdjacentHTML("beforeend", "<p class=\"empty\">No prizes are available yet.</p>");
        return;
      }
      var total = 0;
      res.data.forEach(function (prize) { total += prize.weight; });
      var rows = res.data.map(function (prize) {
        var chance = (prize.weight / total * 100).toFixed(1) + "%";
        var name = prize.is_win ? escapeHtml(prize.name) : "No prize (" + escapeHtml(prize.name) + ")";
        return "<tr><td>" + name + "</td><td>" + escapeHtml(prize.description) +
          "</td><td>" + chance + "</td></tr>";
      }).join("");
      panel.insertAdjacentHTML("beforeend",
        "<table><thead><tr><th>Prize</th><th>Description</th><th>Chance</th></tr></thead>" +
        "<tbody>" + rows + "</tbody></table>");
    }).catch(function () {
      panel.insertAdjacentHTML("beforeend", "<p class=\"empty\">Something went wrong. Please try again.</p>");
    });
  }

  function renderMyWinningsPage(app) {
    var panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML = "<h2>My Winnings</h2><p class=\"notice\">Loading...</p>";
    app.appendChild(panel);
    requestJson("GET", "/api/winnings").then(function (res) {
      panel.innerHTML = "<h2>My Winnings</h2>";
      if (!res.ok) {
        panel.insertAdjacentHTML("beforeend", "<p class=\"empty\">Something went wrong. Please try again.</p>");
        return;
      }
      if (!res.data.length) {
        panel.insertAdjacentHTML("beforeend",
          "<p class=\"empty\">You have no winnings yet. " +
          "<a href=\"#/spin\">Spin the wheel to win a prize!</a></p>");
        return;
      }
      var rows = res.data.map(function (record) {
        var when = new Date(record.won_at).toLocaleString("en-US");
        return "<tr><td>" + escapeHtml(when) + "</td><td>" + escapeHtml(record.prize_name) +
          "</td><td>" + escapeHtml(record.display_name) + "</td></tr>";
      }).join("");
      panel.insertAdjacentHTML("beforeend",
        "<table><thead><tr><th>Won at</th><th>Prize</th><th>Name</th></tr></thead>" +
        "<tbody>" + rows + "</tbody></table>");
    }).catch(function () {
      panel.insertAdjacentHTML("beforeend", "<p class=\"empty\">Something went wrong. Please try again.</p>");
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[ch];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    window.addEventListener("hashchange", route);
    if (!window.location.hash) {
      window.location.replace("#/spin");
    }
    route();
  });
})();
