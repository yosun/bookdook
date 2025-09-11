#!/usr/bin/env python
import argparse
import os

from app.features.letter_explainer import explain_letter


def main():
    parser = argparse.ArgumentParser(description="Letter Explainer -> summary + checklist")
    parser.add_argument("--in", dest="input_path", required=True, help="Input PDF/TXT path")
    parser.add_argument("--out", dest="out_txt", default=None, help="Optional output .txt path")
    args = parser.parse_args()

    res = explain_letter(args.input_path)
    output = f"Summary\n{res.summary}\n\nChecklist\n{res.checklist}\n"
    if args.out_txt:
        os.makedirs(os.path.dirname(args.out_txt) or ".", exist_ok=True)
        with open(args.out_txt, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {args.out_txt}")
    else:
        print(output)


if __name__ == "__main__":
    main()

