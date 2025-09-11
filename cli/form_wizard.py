#!/usr/bin/env python
import argparse
import os

from app.features.form_helper import fill_form_to_pdf


def main():
    parser = argparse.ArgumentParser(description="Form Helper -> schema Q&A -> filled PDF")
    parser.add_argument("--schema", required=True, help="YAML schema file")
    parser.add_argument("--out", required=True, help="Output PDF path")
    parser.add_argument("--interactive", action="store_true", help="Ask user for answers instead of autofill")
    args = parser.parse_args()

    out_pdf, answers = fill_form_to_pdf(args.schema, args.out, interactive=args.interactive)
    print(f"Wrote {out_pdf}")
    # Also write a JSON sidecar for transparency
    sidecar = os.path.splitext(out_pdf)[0] + ".json"
    try:
        import json

        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump(answers, f, ensure_ascii=False, indent=2)
        print(f"Wrote {sidecar}")
    except Exception:
        pass


if __name__ == "__main__":
    main()

