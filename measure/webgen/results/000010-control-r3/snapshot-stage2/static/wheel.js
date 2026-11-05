(function () {
  const canvas = document.getElementById("wheel");
  const ctx = canvas.getContext("2d");
  const spinForm = document.getElementById("spin-form");
  const spinBtn = document.getElementById("spin-btn");
  const nameInput = document.getElementById("player-name");
  const message = document.getElementById("message");
  const SIZE = canvas.width;
  const CENTER = SIZE / 2;
  const RADIUS = CENTER - 10;
  const SPIN_MS = 5000;

  // Alternating segment colors: dark green (white text) and ivory (dark green text).
  const SEGMENT_STYLES = [
    { fill: "#006400", text: "#ffffff" },
    { fill: "#fffff0", text: "#006400" },
    { fill: "#2e7d32", text: "#ffffff" },
    { fill: "#e4efd9", text: "#003300" },
  ];

  let prizes = [];
  let rotation = 0; // total wheel rotation in degrees (keeps growing so the CSS transition always moves)
  let spinning = false;

  function drawWheel() {
    ctx.clearRect(0, 0, SIZE, SIZE);
    const n = prizes.length;
    if (n === 0) return;
    const step = (2 * Math.PI) / n;

    prizes.forEach((prize, i) => {
      // Segment i starts at the top (-90deg) and runs clockwise.
      const a0 = -Math.PI / 2 + i * step;
      const a1 = a0 + step;
      const style = SEGMENT_STYLES[i % SEGMENT_STYLES.length];

      ctx.beginPath();
      ctx.moveTo(CENTER, CENTER);
      ctx.arc(CENTER, CENTER, RADIUS, a0, a1);
      ctx.closePath();
      ctx.fillStyle = style.fill;
      ctx.fill();
      ctx.strokeStyle = "#003300";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw the label along the segment's center line. On the left half of the
      // wheel the text would be upside down, so flip it and anchor it on the other side.
      const mid = a0 + step / 2;
      const flip = Math.cos(mid) < 0;
      ctx.save();
      ctx.translate(CENTER, CENTER);
      ctx.rotate(flip ? mid + Math.PI : mid);
      ctx.fillStyle = style.text;
      ctx.font = "bold 17px Arial, Helvetica, sans-serif";
      ctx.textBaseline = "middle";
      if (flip) {
        ctx.textAlign = "left";
        ctx.fillText(prize.name, -(RADIUS - 22), 0, RADIUS - 80);
      } else {
        ctx.textAlign = "right";
        ctx.fillText(prize.name, RADIUS - 22, 0, RADIUS - 80);
      }
      ctx.restore();
    });

    // Hub
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, 30, 0, 2 * Math.PI);
    ctx.fillStyle = "#003300";
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = "#ffffff";
    ctx.stroke();
  }

  function setMessage(html, isError) {
    message.classList.toggle("error", !!isError);
    message.replaceChildren(...html);
  }

  function resultNodes(player, prize) {
    if (prize.is_win) {
      return [
        WOF.el("p", { class: "win-title", text: player + " won: " + prize.name + "!" }),
        WOF.el("div", null, [
          "Saved to your records with today's date. See them on ",
          WOF.el("a", { href: "/records", text: "My Winning Records" }),
          ".",
        ]),
      ];
    }
    return [
      WOF.el("p", { class: "win-title", text: "No prize this time, " + player + "." }),
      WOF.el("div", { text: "Enter your name and press SPIN to try again." }),
    ];
  }

  function setNameInvalid(invalid) {
    nameInput.setAttribute("aria-invalid", invalid ? "true" : "false");
  }

  async function loadPrizes() {
    try {
      const data = await WOF.api("/api/prizes");
      prizes = data.prizes;
      drawWheel();
    } catch (err) {
      setMessage([err.message], true);
    }
  }

  function spinToTarget(index) {
    const n = prizes.length;
    const step = 360 / n;
    // Land somewhere inside the winning segment, not always on its exact center.
    const jitter = (Math.random() * 0.6 - 0.3) * step;
    // The segment's center sits at angle -(index+0.5)*step relative to the pointer at the top.
    const target = -(index + 0.5) * step + jitter;
    const delta = (((target - rotation) % 360) + 360) % 360;
    rotation += 360 * 6 + delta;
    canvas.style.transition = `transform ${SPIN_MS}ms cubic-bezier(0.17, 0.67, 0.12, 0.99)`;
    canvas.style.transform = `rotate(${rotation}deg)`;
  }

  async function spin() {
    if (spinning) return;
    const player = nameInput.value.trim();
    if (!player) {
      // Required name missing: show a validation message and do not spin.
      setNameInvalid(true);
      setMessage(["Please enter your name before spinning."], true);
      nameInput.focus();
      return;
    }
    setNameInvalid(false);
    if (prizes.length === 0) {
      setMessage(["The prize list is not available yet. Please reload the page."], true);
      return;
    }

    spinning = true;
    spinBtn.disabled = true;
    WOF.setPlayer(player);
    setMessage(["Spinning..."], false);

    let result;
    try {
      result = await WOF.api("/api/spin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player }),
      });
    } catch (err) {
      setMessage([err.message], true);
      spinning = false;
      spinBtn.disabled = false;
      return;
    }

    const index = prizes.findIndex((p) => p.id === result.prize.id);
    spinToTarget(index < 0 ? 0 : index);

    setTimeout(() => {
      setMessage(resultNodes(result.spin.player, result.prize), false);
      spinning = false;
      spinBtn.disabled = false;
    }, SPIN_MS + 150);
  }

  // SPIN button and Enter in the name box both submit this form.
  spinForm.addEventListener("submit", (e) => {
    e.preventDefault();
    spin();
  });
  nameInput.addEventListener("input", () => {
    if (nameInput.value.trim()) setNameInvalid(false);
  });

  const saved = WOF.getPlayer();
  if (saved) nameInput.value = saved;

  drawWheel();
  loadPrizes();
})();
