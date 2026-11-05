# Barber Shop Manager

A small website to browse and add barbers (staff) and services (menu items), and to prepare WhatsApp messages for clients.

## 起動方法 (Getting started)

Requirements: Python 3.9 or later (Python 3.12 recommended). No third-party packages are needed.

1. Set up once:

   ```bash
   bash setup.sh
   ```

2. Start the site (runs in the foreground; stop with Ctrl+C):

   ```bash
   PORT=8000 bash run.sh
   ```

3. Open <http://127.0.0.1:8000/> in a browser.

### Settings

| Name | Meaning | Default |
|---|---|---|
| `PORT` | Port to listen on (on 127.0.0.1) | `8000` |
| `DATA_DIR` | Folder for the database file `barbershop.db` (created if missing) | `./data` |

### Sample data

When the database is created for the first time, the site adds 3 sample barbers and 4 sample services, so every screen has content. No login is needed (there are no user accounts).

## Using the site

- **Home**: links to the three features.
- **Barbers**: list of barbers, and **Add barber**.
- **Services**: list of services with price and duration, and **Add service**.
- **Notify**: enter one or more phone numbers (with country code, one per line or separated by commas, up to 20) and a message. The site creates one **Open in WhatsApp** link per number. Click the link, then send the message in WhatsApp. The site does not send messages itself and does not keep a history.

Prices are shown as plain numbers (for example `25.00`), without a currency symbol.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml
```

## Design documents

The requirements and design are in `docs/requirements.md`, `docs/detail_design.md`, and the trace map in `docs/trace_map.md`.
