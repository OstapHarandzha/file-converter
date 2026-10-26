import json
from pathlib import Path

import pytest

from converter import ConversionRequest, InvalidInputError, execute
from converter.data import csv_to_json, json_to_csv, read_csv

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_csv_to_json_keeps_polish_chars_empty_values_and_column_order(tmp_path):
    target = tmp_path / "out.json"
    csv_to_json(SAMPLES / "osoby.csv", target)

    records = load_json(target)
    assert len(records) == 3
    assert list(records[0]) == ["imię", "nazwisko", "miasto", "e-mail", "uwagi"]
    assert records[0]["miasto"] == "Łódź"
    assert records[0]["uwagi"] == ""
    assert records[1]["uwagi"] == "Lubi kawę, herbatę i żurek"
    assert records[2]["uwagi"] == 'Powiedziała: "Dzień dobry"'


def test_csv_with_semicolon_delimiter_keeps_values_as_text(tmp_path):
    target = tmp_path / "out.json"
    csv_to_json(SAMPLES / "produkty_excel.csv", target)

    records = load_json(target)
    assert records[0] == {"kod": "007", "produkt": "Jabłko", "cena": "2,50", "ilość": "10"}
    assert records[1]["cena"] == ""


def test_csv_json_csv_round_trip_gives_same_table(tmp_path):
    json_file = tmp_path / "data.json"
    csv_file = tmp_path / "data.csv"
    csv_to_json(SAMPLES / "osoby.csv", json_file)
    json_to_csv(json_file, csv_file)

    assert read_csv(csv_file) == read_csv(SAMPLES / "osoby.csv")


def test_json_to_csv_collects_all_columns_and_fills_missing_values(tmp_path):
    target = tmp_path / "out.csv"
    json_to_csv(SAMPLES / "produkty.json", target)

    header, rows = read_csv(target)
    assert header == ["id", "nazwa", "cena", "dostępny", "kategoria"]
    assert rows == [
        ["1", "Żółty ser", "24.99", "true", ""],
        ["2", "Chleb żytni", "", "false", ""],
        ["3", "Mąka", "", "", "Sypkie"],
    ]


def test_csv_output_has_bom_for_excel(tmp_path):
    target = tmp_path / "out.csv"
    json_to_csv(SAMPLES / "produkty.json", target)
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")


def test_broken_json_gives_controlled_error_with_position(tmp_path):
    with pytest.raises(InvalidInputError, match=r"wiersz 2"):
        json_to_csv(SAMPLES / "uszkodzony.json", tmp_path / "out.csv")


@pytest.mark.parametrize(
    "content, fragment",
    [
        ('{"a": 1}', "listę obiektów"),
        ("[]", "pusta"),
        ("[1, 2]", "nie jest obiektem"),
        ('[{"a": {"b": 1}}]', "zagnieżdżone"),
        ("", "pusty"),
    ],
    ids=["top-level-object", "empty-list", "items-not-objects", "nested-values", "empty-file"],
)
def test_json_with_unsupported_structure_is_rejected(tmp_path, content, fragment):
    source = tmp_path / "in.json"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidInputError, match=fragment):
        json_to_csv(source, tmp_path / "out.csv")


@pytest.mark.parametrize(
    "content, fragment",
    [
        ("", "pusty"),
        ("a,b\n1,2,3\n", "Wiersz 2: 3 pól zamiast 2"),
        ("a,a\n1,2\n", "Powtórzone"),
        ("a,\n1,2\n", "pustą nazwę"),
    ],
    ids=["empty-file", "too-many-fields", "duplicate-header", "empty-column-name"],
)
def test_invalid_csv_is_rejected(tmp_path, content, fragment):
    source = tmp_path / "in.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidInputError, match=fragment):
        csv_to_json(source, tmp_path / "out.json")


def test_non_utf8_csv_is_rejected(tmp_path):
    source = tmp_path / "in.csv"
    source.write_bytes("miasto\nŁódź\n".encode("cp1250"))
    with pytest.raises(InvalidInputError, match="UTF-8"):
        csv_to_json(source, tmp_path / "out.json")


def test_failed_conversion_does_not_touch_existing_target(tmp_path):
    existing = tmp_path / "uszkodzony.csv"
    existing.write_text("old content", encoding="utf-8")
    request = ConversionRequest(SAMPLES / "uszkodzony.json", ".csv", tmp_path, overwrite=True)

    with pytest.raises(InvalidInputError):
        execute(request)
    assert existing.read_text(encoding="utf-8") == "old content"
    assert [p.name for p in tmp_path.iterdir()] == ["uszkodzony.csv"]
