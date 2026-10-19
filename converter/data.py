"""Group A - structured data: CSV <-> JSON.

Semantics (also described in README):
* Input encoding: UTF-8 (with or without BOM).
* CSV: the first non-empty row is the header; column names must be non-empty
  and unique. Delimiter is detected from the header line: ',', ';' or tab.
  Every data row must have exactly as many fields as the header.
* JSON: a list of flat objects, e.g. [{"name": "Anna", "age": 30}, ...].
  Values must be text, numbers, true/false or null - no nested objects/lists.
* CSV -> JSON: every value becomes a string (no type guessing, so "007"
  stays "007"); an empty cell becomes "".
* JSON -> CSV: columns are all keys in order of first appearance; a missing
  key or null becomes an empty cell; true/false are written as "true"/"false".
  Output uses ',' and UTF-8 with BOM, so Excel displays Polish characters.
"""
import csv
import io
import json
from pathlib import Path

from .registry import InvalidInputError, converter

DELIMITERS = (",", ";", "\t")


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise InvalidInputError(
            f"Plik {path.name} nie jest zapisany w kodowaniu UTF-8.",
            "Zapisz plik ponownie jako UTF-8 (np. w Excelu: 'CSV UTF-8').",
        ) from error


def detect_delimiter(header_line: str) -> str:
    counts = {delimiter: header_line.count(delimiter) for delimiter in DELIMITERS}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return (header, rows) and check that the table is consistent."""
    text = read_utf8(path)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise InvalidInputError("Plik CSV jest pusty.", "Wybierz plik zawierający nagłówek i dane.")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=detect_delimiter(lines[0]))
    try:
        rows = [(reader.line_num, row) for row in reader if row]
    except csv.Error as error:
        raise InvalidInputError(
            f"Niepoprawny format CSV (wiersz {reader.line_num}): {error}",
            "Sprawdź cudzysłowy i separatory w tym wierszu.",
        ) from error

    _, header = rows[0]
    if any(not name.strip() for name in header):
        raise InvalidInputError("Nagłówek CSV zawiera pustą nazwę kolumny.", "Nadaj nazwę każdej kolumnie.")
    duplicates = sorted({name for name in header if header.count(name) > 1})
    if duplicates:
        raise InvalidInputError(
            f"Powtórzone nazwy kolumn: {', '.join(duplicates)}",
            "Nazwy kolumn muszą być unikalne.",
        )

    for line_number, row in rows[1:]:
        if len(row) != len(header):
            raise InvalidInputError(
                f"Wiersz {line_number}: {len(row)} pól zamiast {len(header)}.",
                "Popraw liczbę separatorów; wartości zawierające separator ujmij w cudzysłów.",
            )
    return header, [row for _, row in rows[1:]]


def read_json_records(path: Path) -> list[dict]:
    """Load and validate a JSON file in the accepted structure (list of flat objects)."""
    text = read_utf8(path)
    if not text.strip():
        raise InvalidInputError("Plik JSON jest pusty.", "Wybierz plik zawierający listę obiektów.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise InvalidInputError(
            f"Niepoprawny JSON (wiersz {error.lineno}, kolumna {error.colno}): {error.msg}",
            "Popraw składnię pliku, np. w edytorze z walidacją JSON.",
        ) from error

    expected = 'Oczekiwana struktura: [{"kolumna": "wartość", ...}, ...].'
    if not isinstance(data, list):
        raise InvalidInputError("JSON musi zawierać listę obiektów na najwyższym poziomie.", expected)
    if not data:
        raise InvalidInputError("Lista w pliku JSON jest pusta - brak danych do zapisania.", expected)
    for number, record in enumerate(data, start=1):
        if not isinstance(record, dict):
            raise InvalidInputError(f"Element nr {number} nie jest obiektem.", expected)
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                raise InvalidInputError(
                    f"Rekord nr {number}, pole '{key}': zagnieżdżone obiekty i listy nie są obsługiwane.",
                    expected,
                )
    return data


def to_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value)  # numbers and true/false in JSON notation


@converter(".csv", ".json")
def csv_to_json(source: Path, target: Path) -> None:
    header, rows = read_csv(source)
    records = [dict(zip(header, row)) for row in rows]
    with target.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
        file.write("\n")


@converter(".json", ".csv")
def json_to_csv(source: Path, target: Path) -> None:
    records = read_json_records(source)
    columns = list(dict.fromkeys(key for record in records for key in record))
    with target.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for record in records:
            writer.writerow([to_cell(record.get(column)) for column in columns])
