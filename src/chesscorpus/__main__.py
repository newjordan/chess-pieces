"""Command line for validating and rebuilding the corpus."""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
from pathlib import Path

from chesscorpus.corpus import normalize_corpus, render_corpus, report_corpus, validation_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chesscorpus")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="corpus root (the directory that contains catalog.json)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="check manifests, meshes, and previews")
    commands.add_parser("normalize", help="rewrite GLBs so every piece is game-ready")
    commands.add_parser("render", help="rewrite preview PNGs from the GLBs")
    commands.add_parser("report", help="print measured mesh stats as a markdown table")
    preview = commands.add_parser("preview", help="serve the corpus and open the gallery")
    preview.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.command == "validate":
        errors = validation_errors(root)
        if errors:
            for error in errors:
                print(error)
            print(f"{len(errors)} error(s)")
            return 1
        print(f"OK {root}")
        return 0
    if args.command == "normalize":
        normalize_corpus(root)
        return 0
    if args.command == "render":
        render_corpus(root)
        return 0
    if args.command == "report":
        print(report_corpus(root))
        return 0
    _serve(root, args.port)
    return 0


def _serve(root: Path, port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    print(f"Gallery at http://127.0.0.1:{port}/preview/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
