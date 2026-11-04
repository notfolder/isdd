# Polls

A small polls website. Browse polls, cast one vote per poll, and view the results.

## 起動方法 (Start)

```bash
bash setup.sh                 # once: creates .venv and installs Flask
PORT=8000 bash run.sh         # starts the server in the foreground
```

Open http://127.0.0.1:8000/ in a browser. Stop the server with Ctrl+C.

- `PORT` (default 8000): the port on 127.0.0.1.
- `DATA_DIR` (default `data/` in the project folder): where `polls.db` is stored. If it is empty, the site starts with sample polls and votes.

## Pages

- Polls (`/`): the list of polls. Open a poll to vote.
- Poll (`/polls/<id>`): choose one option and press Vote. After voting, the options and the Vote button are disabled, the page shows "You have already voted", and the results of that poll are shown. One vote per poll per browser.
- Create poll (`/polls/new`): enter a question and at least two options (up to four option boxes; empty boxes are ignored) and press Create poll. The new poll appears in the poll list and on the results page at once, and you are taken to its page to vote. Questions are at most 200 characters, options at most 100, and options must differ.
- Results (`/results`): the vote counts and shares of every poll.

## Tests

```bash
.venv/bin/python -m pytest tests                                  # unit tests
.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml     # end-to-end tests
```
