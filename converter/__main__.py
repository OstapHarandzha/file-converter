"""Command-line mode (no GUI).

Examples:
    python -m converter --list
    python -m converter samples/osoby.csv json -o output
    python -m converter samples/produkty.json csv -o output --overwrite
"""
import argparse
import sys
from pathlib import Path

from . import ConversionError, ConversionRequest, execute, supported_pairs
from .app_logging import LOG_FILE, setup_logging


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")  # consoles without UTF-8 must not crash
    setup_logging()

    parser = argparse.ArgumentParser(prog="python -m converter", description="Konwerter plików - tryb bez GUI.")
    parser.add_argument("source", nargs="?", type=Path, help="plik wejściowy")
    parser.add_argument("target_format", nargs="?", help="format docelowy, np. json lub .json")
    parser.add_argument("-o", "--output-dir", type=Path, help="katalog zapisu (domyślnie katalog pliku wejściowego)")
    parser.add_argument("--overwrite", action="store_true", help="nadpisz istniejący plik zamiast tworzyć nową nazwę")
    parser.add_argument("--list", action="store_true", help="pokaż obsługiwane konwersje")
    args = parser.parse_args(argv)

    if args.list:
        for source, target in supported_pairs():
            print(f"{source} -> {target}")
        return 0
    if args.source is None or not args.target_format:
        parser.error("podaj plik wejściowy i format docelowy (albo użyj --list)")

    if args.output_dir is not None:
        try:
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            print(f"Błąd: nie można utworzyć katalogu {args.output_dir}: {error}", file=sys.stderr)
            return 1

    target_format = args.target_format.lower()
    if not target_format.startswith("."):
        target_format = "." + target_format
    request = ConversionRequest(
        source=args.source,
        target_format=target_format,
        output_dir=args.output_dir or args.source.parent,
        overwrite=args.overwrite,
    )
    try:
        result = execute(request)
    except ConversionError as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Nieoczekiwany błąd: {error}\nSzczegóły w pliku {LOG_FILE}", file=sys.stderr)
        return 2
    print(f"Zapisano: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
