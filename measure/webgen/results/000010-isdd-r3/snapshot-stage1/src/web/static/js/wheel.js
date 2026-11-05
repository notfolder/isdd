// Spin page: draws the prize wheel, asks the server for the result, and animates the wheel to it.

var TWO_PI = Math.PI * 2;
var SPIN_TURNS = 6;
var SPIN_DURATION_MS = 4000;
var WHEEL_COLORS = ['#8B0000', '#F5F5F5'];
var WHEEL_TEXT_COLORS = ['#FFFFFF', '#8B0000'];

var wheelSegments = [];
var wheelAngle = 0;
var spinning = false;

// Start the spin page: restore the saved name, load the prizes, and bind the Spin button.
function initSpinPage() {
  const nameInput = document.getElementById('player-name');
  const spinButton = document.getElementById('spin-button');
  const canvas = document.getElementById('wheel');
  nameInput.value = localStorage.getItem('wheel.playerName') || '';
  spinButton.addEventListener('click', startSpin);
  fetchJson('/api/prizes')
    .then(function (prizes) {
      wheelSegments = prizes;
      drawWheel(canvas, wheelSegments, wheelAngle);
    })
    .catch(function () {
      document.getElementById('error-message').textContent = 'Could not load prizes.';
    });
}

// Draw every segment clockwise from the top; the pointer is at the top.
function drawWheel(canvas, segments, angle) {
  const context = canvas.getContext('2d');
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 4;
  const step = TWO_PI / Math.max(segments.length, 1);
  context.clearRect(0, 0, canvas.width, canvas.height);
  segments.forEach(function (segment, index) {
    const start = -Math.PI / 2 + angle + index * step;
    const colorIndex = index % WHEEL_COLORS.length;
    context.beginPath();
    context.moveTo(centerX, centerY);
    context.arc(centerX, centerY, radius, start, start + step);
    context.closePath();
    context.fillStyle = WHEEL_COLORS[colorIndex];
    context.fill();
    context.strokeStyle = '#8B0000';
    context.lineWidth = 2;
    context.stroke();
    drawSegmentLabel(context, segment, centerX, centerY, radius, start + step / 2, colorIndex);
  });
  context.beginPath();
  context.arc(centerX, centerY, 22, 0, TWO_PI);
  context.fillStyle = '#8B0000';
  context.fill();
  context.beginPath();
  context.moveTo(centerX - 12, 4);
  context.lineTo(centerX + 12, 4);
  context.lineTo(centerX, 28);
  context.closePath();
  context.fillStyle = '#222222';
  context.fill();
}

// Write one segment's label along its middle angle. Labels on the left half are turned
// so they read from left to right, and a long label is shrunk to fit between the centre and the rim.
function drawSegmentLabel(context, segment, centerX, centerY, radius, middle, colorIndex) {
  const label = segment.is_miss ? 'Try again' : segment.name;
  const available = radius - 40;
  const flip = Math.cos(middle) < 0;
  context.save();
  context.translate(centerX, centerY);
  context.rotate(flip ? middle + Math.PI : middle);
  context.fillStyle = WHEEL_TEXT_COLORS[colorIndex];
  context.textAlign = flip ? 'left' : 'right';
  context.font = 'bold 14px system-ui, sans-serif';
  if (context.measureText(label).width > available) {
    const size = Math.max(8, Math.floor(14 * available / context.measureText(label).width));
    context.font = 'bold ' + size + 'px system-ui, sans-serif';
  }
  const x = flip ? -(radius - 14) : radius - 14;
  context.fillText(label, x, 5);
  context.restore();
}

// Spin: send the name, animate to the returned segment, then show the result.
async function startSpin() {
  if (spinning) {
    return;
  }
  const nameInput = document.getElementById('player-name');
  const spinButton = document.getElementById('spin-button');
  const errorBox = document.getElementById('error-message');
  const resultBox = document.getElementById('result');
  errorBox.textContent = '';
  resultBox.textContent = '';
  localStorage.setItem('wheel.playerName', nameInput.value.trim());
  spinning = true;
  spinButton.disabled = true;
  try {
    const outcome = await fetchJson('/api/spin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: nameInput.value })
    });
    await animateWheelTo(outcome.segment_index);
    resultBox.textContent = outcome.is_miss ? 'Try again' : 'You won: ' + outcome.prize_name + '!';
  } catch (error) {
    if (error.status === 400) {
      errorBox.textContent = error.message;
    } else {
      resultBox.textContent = error.message;
    }
  } finally {
    spinning = false;
    spinButton.disabled = false;
  }
}

// Turn the wheel so that the centre of the given segment stops under the top pointer.
function animateWheelTo(segmentIndex) {
  const canvas = document.getElementById('wheel');
  const step = TWO_PI / wheelSegments.length;
  const start = wheelAngle;
  const wanted = -(segmentIndex + 0.5) * step;
  const offset = (((wanted - start) % TWO_PI) + TWO_PI) % TWO_PI;
  const target = start + SPIN_TURNS * TWO_PI + offset;
  const startedAt = performance.now();
  return new Promise(function (resolve) {
    function frame(now) {
      const progress = Math.min(1, (now - startedAt) / SPIN_DURATION_MS);
      const eased = 1 - Math.pow(1 - progress, 3);
      wheelAngle = start + (target - start) * eased;
      drawWheel(canvas, wheelSegments, wheelAngle);
      if (progress < 1) {
        requestAnimationFrame(frame);
      } else {
        resolve();
      }
    }
    requestAnimationFrame(frame);
  });
}

document.addEventListener('DOMContentLoaded', initSpinPage);
