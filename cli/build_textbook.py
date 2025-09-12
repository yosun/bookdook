#!/usr/bin/env python
import argparse
import os

from app.features.textbook_builder import TextbookSpec, build_textbook


def main():
    parser = argparse.ArgumentParser(description="Textbook Builder -> EPUB")
    parser.add_argument("--grade", type=int, required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--mode", choices=["sample", "full"], default="sample", help="Generation mode: sample (fast) or full (longer)")
    parser.add_argument("--out", default=None, help="Optional output .epub path")
    args = parser.parse_args()

    out = args.out or os.path.join("out", f"textbook_g{args.grade}_{args.lang}_{args.topic.replace(' ', '_')}.epub")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    spec = TextbookSpec(grade=args.grade, language=args.lang, topic=args.topic)
    path = build_textbook(spec, out, mode=args.mode)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

