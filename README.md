# PlainText.ink MVP

“a $15 offline e-ink omnibook tablet powered by GPT-OSS, built for the 4B people current tech can’t reach.”

This repository provides a runnable MVP with three features and two local LLM backends.

## Features
- Letter Explainer: PDF/TXT to summary + checklist
- Form Helper: schema Q&A to filled PDF
- Textbook Builder: grade/lang/topic to EPUB

## Layout
- `app/` – core logic and backends
- `cli/` – command-line interfaces
- `ui/` – minimal PyQt6 UI (3 tabs)
- `content/` – sample data (letters, forms)
- `safety/` – safety notes
- `tests/` – minimal tests

## Backends (offline)
- `ollama` (default demo): talks to a local Ollama daemon
- `llamacpp` (production): uses `llama-cpp-python` with a local GGUF model

Switch via `PLAIN_BACKEND` env var. If a backend is unavailable, it falls back to a deterministic `dummy` backend for demos/tests.

## Quickstart

### 1. Install dependencies
```bash
# Install Ollama (default demo backend)
brew install ollama   # or see https://ollama.com/download
ollama pull llama3    # small local GPT-OSS model

# Python env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "PLAIN_BACKEND=ollama" >> .env
```

### 2. Run demos
```bash
# Letter Explainer
python cli/explain_letter.py --in content/letters/sample_medi_cal.pdf

# Form Helper
python cli/form_wizard.py --schema content/forms/snap.yaml --out out/filled.pdf

# Textbook Builder
python cli/build_textbook.py --grade 5 --lang es --topic "fractions"
```

Notes:
- If `content/letters/sample_medi_cal.pdf` does not exist, the tool will auto-generate a small demo PDF on first run.
- `out/` is created as needed.

### 3. Optional: llama.cpp backend
```bash
pip install llama-cpp-python
# Place a quantized GGUF model in ./models/
echo "PLAIN_BACKEND=llamacpp" >> .env
echo "LLAMACPP_MODEL_PATH=models/LLAMA3.1-8B-Instruct-Q4_K_M.gguf" >> .env
```

### 4. UI (optional)
```bash
python ui/main_qt.py
```

### 5. Safety
- Offline only: no network I/O.
- Not legal/medical advice.
- Model may hallucinate; always verify outputs.

## Development
- Run tests: `pytest -q`
- Force dummy backend for tests/demos: `export PLAIN_BACKEND=dummy`

## License
MVP code provided as-is for demonstration purposes.

