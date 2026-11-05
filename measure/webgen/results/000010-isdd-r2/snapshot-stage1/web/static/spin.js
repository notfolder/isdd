/* Spin the Wheel 画面: ホイールの描画、名前の検査、抽選の要求、回転と結果の表示。 */
(function () {
  "use strict";

  var app = window.WheelApp;
  var NAME_MAX = 30;
  var SPIN_MS = 4000;
  var SEGMENT_COLORS = ["#8B0000", "#5E0000"];
  var ODD_LAST_COLOR = "#A52A2A";

  var canvas = document.getElementById("wheel");
  var ctx = canvas.getContext("2d");
  var form = document.getElementById("spin-form");
  var input = document.getElementById("player-name");
  var button = document.getElementById("spin-button");
  var nameError = document.getElementById("name-error");
  var result = document.getElementById("result");

  var prizes = [];
  var rotation = 0;
  var spinning = false;

  function shorten(text) {
    return text.length > 20 ? text.slice(0, 19) + "…" : text;
  }

  function drawWheel() {
    var size = canvas.width;
    var center = size / 2;
    var radius = center - 6;
    ctx.clearRect(0, 0, size, size);

    if (prizes.length === 0) {
      ctx.beginPath();
      ctx.arc(center, center, radius, 0, Math.PI * 2);
      ctx.fillStyle = "#8B0000";
      ctx.fill();
      return;
    }

    var count = prizes.length;
    var step = (Math.PI * 2) / count;
    for (var i = 0; i < count; i++) {
      var start = -Math.PI / 2 + i * step;
      var end = start + step;
      var color = SEGMENT_COLORS[i % 2];
      if (count % 2 === 1 && i === count - 1) {
        color = ODD_LAST_COLOR;
      }
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.arc(center, center, radius, start, end);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();

      ctx.save();
      ctx.translate(center, center);
      ctx.rotate(start + step / 2);
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 16px Arial, sans-serif";
      ctx.fillText(shorten(prizes[i].name), radius - 18, 0);
      ctx.restore();
    }

    ctx.beginPath();
    ctx.arc(center, center, 26, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = "#8B0000";
    ctx.stroke();
  }

  /* 指針（画面の上）の下に、抽選された区画の中央が来る回転角（度）。 */
  function stopAngleFor(index) {
    var step = 360 / prizes.length;
    var centerOffset = (index + 0.5) * step;
    return ((360 - centerOffset) % 360 + 360) % 360;
  }

  function spinTo(index) {
    var current = ((rotation % 360) + 360) % 360;
    var delta = (stopAngleFor(index) - current + 360) % 360;
    rotation += 5 * 360 + delta;
    canvas.style.transition = "transform " + SPIN_MS + "ms cubic-bezier(0.17, 0.67, 0.12, 1)";
    canvas.style.transform = "rotate(" + rotation + "deg)";
  }

  function finish() {
    spinning = false;
    button.disabled = false;
  }

  function showResult(data) {
    var prize = data.prize;
    result.textContent = "";

    var heading = document.createElement("h2");
    heading.textContent = "You won " + prize.name + "!";

    var details = document.createElement("p");
    details.textContent = "Congratulations, " + data.record.player_name + ". " + (prize.description || "");

    result.appendChild(heading);
    result.appendChild(details);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (spinning || prizes.length === 0) {
      return;
    }

    var name = input.value.trim();
    if (name === "") {
      app.showError(nameError, "Please enter your name before spinning.");
      input.focus();
      return;
    }
    if (name.length > NAME_MAX) {
      app.showError(nameError, "Name must be 30 characters or fewer.");
      input.focus();
      return;
    }

    app.showError(nameError, "");
    app.saveName(name);
    spinning = true;
    button.disabled = true;
    result.textContent = "Spinning...";

    app.postJSON("/api/spins", { player_name: name }).then(function (data) {
      spinTo(data.prize_index);
      window.setTimeout(function () {
        showResult(data);
        finish();
      }, SPIN_MS + 150);
    }).catch(function (error) {
      result.textContent = "";
      app.showError(nameError, error.message);
      finish();
    });
  });

  input.value = app.loadName();
  drawWheel();

  app.getJSON("/api/prizes").then(function (data) {
    prizes = data.prizes;
    drawWheel();
    if (prizes.length === 0) {
      app.showError(nameError, "No prizes are available right now.");
      button.disabled = true;
    }
  }).catch(function () {
    app.showError(nameError, "The prize list could not be loaded.");
    button.disabled = true;
  });
})();
