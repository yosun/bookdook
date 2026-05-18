# BookDook · PlainText.ink

> *"A $10–$15 offline e‑Ink omnibook tablet powered by Gemma4 — built for the 4 billion people current tech can't reach."*

BookDook is the reference MVP behind **PlainText.ink**: a local‑first, offline reading & writing toolkit that turns a small device + a local LLM (Gemma4 via Ollama by default) into three practical tools — a Letter Explainer, a Form Helper, and a Textbook Builder. It runs as a tiny web app in the browser and as CLI tools, with no network calls beyond `localhost`.

---

## Features

| Tool | What it does | Output |
| --- | --- | --- |
| **Letter Explainer** | Reads a PDF/TXT (e.g. a benefits letter) and produces a plain‑language TL;DR plus a "next steps" checklist. | JSON / printable summary |
| **Form Helper** | Walks a YAML form schema, asks/auto‑fills the answers with the local LLM, and renders a filled PDF. | PDF |
| **Textbook Builder** | Generates an offline‑ready textbook EPUB by grade, language, and topic. `sample` mode is fast; `full` mode is multi‑chapter. | EPUB |

The web UI streams tokens live via Server‑Sent Events, so generation feels responsive even on modest hardware.

## Backends

Selected via the `PLAIN_BACKEND` environment variable:

- **`ollama`** *(default)* — talks to a local Ollama daemon. Default model: **`gemma4:e2b`** (override with `OLLAMA_MODEL`). The backend auto‑resolves to a compatible installed Gemma tag if the exact one isn't present.
- **`llamacpp`** — uses `llama-cpp-python` with a local GGUF file (set `LLAMACPP_MODEL_PATH`).
- **`dummy`** — deterministic stub used by tests and offline demos.

> **Why Gemma4?** Multilingual coverage out of the box, runs on small/cheap devices, and the `e2b` variant is small enough for an e‑Ink class tablet while still producing useful study material and form answers. The Ollama backend explicitly disables hidden chain‑of‑thought (`think=False`) so the limited token budget goes to visible output instead of silent reasoning.

## Repository layout

```
app/
  config.py                  # typed env‑var config (PLAIN_BACKEND, OLLAMA_MODEL, …)
  backends/                  # ollama / llamacpp / dummy backends + factory
  features/
    letter_explainer.py
    form_helper.py
    textbook_builder.py
  utils/                     # pdf + epub helpers
cli/
  serve_frontend.py          # local HTTP + SSE streaming server (port 8000)
  build_textbook.py
  explain_letter.py
  form_wizard.py
layout/page.html             # the local web UI
site/index.html              # public landing page
content/                     # sample letter + sample form schema
ui/main_qt.py                # optional PyQt6 desktop UI
tests/                       # pytest suite (uses the dummy backend)
```

## Quickstart

### 1. Install Ollama and pull Gemma4

```bash
# macOS
brew install ollama
ollama serve &                # leave running

# Pull the default Gemma4 model used by BookDook
ollama pull gemma4:e2b
```

> Any Gemma family tag works — set `OLLAMA_MODEL` to override (e.g. `gemma4:4b`, `gemma2:2b`). If the configured tag isn't installed, BookDook falls back to the closest matching `gemma*` tag you have locally.

### 2. Set up the Python env

```bash
git clone https://github.com/yosun/bookdook.git
cd bookdook/BookDook
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "ollama>=0.3.1"        # or:  pip install -e ".[ollama]"

cp .env.example .env
echo "PLAIN_BACKEND=ollama"    >> .env
echo "OLLAMA_MODEL=gemma4:e2b" >> .env
```

### 3. Run the web app

```bash
make serve
# or:
./.venv/bin/python cli/serve_frontend.py
```

Open <http://127.0.0.1:8000/layout/page.html>.

The same server exposes a small JSON API:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/generate` | One‑shot text generation |
| `POST` | `/api/generate_stream` | SSE token stream |
| `POST` | `/api/explain_letter` | Summarize a local PDF/TXT |
| `POST` | `/api/build_textbook` | Build an EPUB (`mode: sample \| full`) |
| `POST` | `/api/form_fill` | Fill a YAML‑defined form to PDF |

### 4. CLI usage

```bash
# Letter Explainer (auto‑creates a demo PDF on first run)
./.venv/bin/python cli/explain_letter.py --in content/letters/sample_medi_cal.pdf

# Form Helper
./.venv/bin/python cli/form_wizard.py --schema content/forms/snap.yaml --out out/filled.pdf

# Textbook Builder
./.venv/bin/python cli/build_textbook.py --grade 5 --lang es --topic "fractions" --mode sample
./.venv/bin/python cli/build_textbook.py --grade 5 --lang es --topic "fractions" --mode full
```

`out/` is created automatically.

### 5. Optional — llama.cpp backend

```bash
pip install "bookdook[llamacpp]"            # or: pip install llama-cpp-python
echo "PLAIN_BACKEND=llamacpp"                          >> .env
echo "LLAMACPP_MODEL_PATH=models/your-model.gguf"      >> .env
```

### 6. Optional — PyQt6 desktop UI

```bash
pip install "bookdook[ui]"
./.venv/bin/python ui/main_qt.py
```

## Configuration reference

All settings come from environment variables (loaded from `.env` if present):

| Variable | Default | Notes |
| --- | --- | --- |
| `PLAIN_BACKEND` | `ollama` | `ollama`, `llamacpp`, or `dummy` |
| `PLAIN_MAX_TOKENS` | `512` | Cap per generation call |
| `PLAIN_TEMPERATURE` | `0.2` | |
| `PLAIN_TOP_P` | `0.9` | |
| `OLLAMA_MODEL` | `gemma4:e2b` | Any `gemma*` tag works |
| `OLLAMA_HOST` / `OLLAMA_PORT` | `127.0.0.1` / `11434` | |
| `LLAMACPP_MODEL_PATH` | — | Required for the llama.cpp backend |
| `LLAMACPP_CTX_SIZE` | `2048` | |
| `LLAMACPP_N_THREADS` | `4` | |
| `BOOKDOOK_HOST` / `PORT` | `127.0.0.1` / `8000` | Web server bind |
| `BOOKDOOK_LOG_LEVEL` | `INFO` | |

## Development

```bash
make install           # pip install -r requirements.txt
make test              # pytest -q  (runs against the dummy backend)
make lint              # ruff check .
make serve             # launch the local web app
```

Force the deterministic backend for tests and demos with `export PLAIN_BACKEND=dummy`.

Requires **Python ≥ 3.11**.

## Safety & scope

- **Offline only** — the app never makes outbound network calls; only `localhost` traffic to your LLM runtime.
- **Not legal or medical advice.** Outputs from a local LLM can be wrong or out of date — always verify before acting on a letter, form, or lesson.
- Models can hallucinate, especially in lower‑resource languages. Treat generated textbooks as a starting draft for a teacher or parent to review.

See [`safety/README.md`](safety/README.md) for the full notes.

## License

MIT — see [`LICENSE`](LICENSE). MVP code provided as‑is for demonstration purposes.
