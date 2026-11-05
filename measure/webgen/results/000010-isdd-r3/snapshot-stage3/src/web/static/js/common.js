// Shared helpers for the three pages. Plain JavaScript, no build step.

var SERVER_ERROR_MESSAGE = 'Something went wrong. Please try again.';

// Call the API and return the parsed JSON body.
// Throws an Error with .status: the HTTP status, or 0 when the request never got a response.
async function fetchJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (networkError) {
    const failure = new Error(SERVER_ERROR_MESSAGE);
    failure.status = 0;
    throw failure;
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const failure = new Error(body && body.error ? body.error : SERVER_ERROR_MESSAGE);
    failure.status = response.status;
    throw failure;
  }
  return body;
}

// Escape text before putting it into HTML.
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, function (character) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[character];
  });
}
