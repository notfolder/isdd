"""HTTP layer: routes, form handling and redirects (Post/Redirect/Get)."""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import os

from core.validation import ValidationError, validate_barber_form, validate_notify_form, validate_service_form
from core.whatsapp import build_whatsapp_link
from web import views

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
MAX_BODY_BYTES = 64 * 1024


class AppHandler(BaseHTTPRequestHandler):
    """Routes requests to the screens. The store is read from the server object."""

    server_version = "BarberShop/1.0"

    @property
    def store(self):
        """The Store shared by all requests (set on the server)."""
        return self.server.store

    def log_message(self, format, *args):
        """Do not write an access log (the requirements do not ask for logs)."""
        return

    def do_GET(self):
        """Serve a screen or static file for a GET request."""
        path = urlsplit(self.path).path.rstrip("/") or "/"
        try:
            if path == "/":
                html = views.render_home(len(self.store.list_barbers()), len(self.store.list_services()))
                return self._send_html(200, html)
            if path == "/barbers":
                return self._send_html(200, views.render_barber_list(self.store.list_barbers()))
            if path == "/barbers/new":
                return self._send_html(200, views.render_barber_form({}, []))
            if path == "/services":
                return self._send_html(200, views.render_service_list(self.store.list_services()))
            if path == "/services/new":
                return self._send_html(200, views.render_service_form({}, []))
            if path == "/notify":
                return self._send_html(200, views.render_notify_form({}))
            if path == "/static/style.css":
                return self._send_static("style.css", "text/css; charset=utf-8")
            return self._send_html(404, views.render_layout("Not found", "", "<p>The page was not found.</p>"))
        except Exception:
            return self._send_server_error()

    def do_POST(self):
        """Handle the three form submissions."""
        path = urlsplit(self.path).path.rstrip("/") or "/"
        try:
            form = self._read_form()
            if path == "/barbers":
                return self._post_barber(form)
            if path == "/services":
                return self._post_service(form)
            if path == "/notify":
                return self._post_notify(form)
            return self._send_html(404, views.render_layout("Not found", "", "<p>The page was not found.</p>"))
        except Exception:
            return self._send_server_error()

    def _post_barber(self, form):
        """Validate and save a barber, then redirect to the list."""
        values = {k: form.get(k, "") for k in ("name", "specialty", "phone")}
        try:
            data = validate_barber_form(values)
        except ValidationError as err:
            return self._send_html(400, views.render_barber_form(values, err.errors))
        self.store.add_barber(data["name"], data["specialty"], data["phone"])
        return self._redirect("/barbers")

    def _post_service(self, form):
        """Validate and save a service, then redirect to the list."""
        values = {k: form.get(k, "") for k in ("name", "price", "duration_min", "description")}
        try:
            data = validate_service_form(values)
        except ValidationError as err:
            return self._send_html(400, views.render_service_form(values, err.errors))
        self.store.add_service(data["name"], data["price_cents"], data["duration_min"], data["description"])
        return self._redirect("/services")

    def _post_notify(self, form):
        """Validate the numbers and message, then show one WhatsApp link per number."""
        values = {"phones": form.get("phones", ""), "message": form.get("message", "")}
        try:
            data = validate_notify_form(values)
        except ValidationError as err:
            return self._send_html(400, views.render_notify_form(values, err.errors))
        links = [(digits, build_whatsapp_link(digits, data["message"])) for digits in data["numbers"]]
        return self._send_html(200, views.render_notify_form(values, [], links))

    def _read_form(self):
        """Read an urlencoded POST body into a dict of first values."""
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            raise ValueError("body too large")
        raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
        parsed = parse_qs(raw, keep_blank_values=True)
        return {key: values[0] for key, values in parsed.items()}

    def _send_html(self, status, html):
        """Send an HTML response."""
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_static(self, name, content_type):
        """Send a file from the static directory."""
        with open(os.path.join(STATIC_DIR, name), "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location):
        """Send a 303 redirect after a successful save."""
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_server_error(self):
        """Send a generic English error page (details go to the console)."""
        import traceback
        traceback.print_exc()
        html = views.render_layout("Error", "", "<p>Something went wrong. Please try again.</p>")
        self._send_html(500, html)
