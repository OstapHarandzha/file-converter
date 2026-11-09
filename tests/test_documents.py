import sys
import zipfile
from pathlib import Path

import docx
import pytest

from converter import ConversionRequest, InvalidInputError, MissingDependencyError, execute

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def paragraphs(path: Path) -> list[str]:
    return [paragraph.text for paragraph in docx.Document(path).paragraphs]


def test_txt_to_docx_keeps_lines_as_paragraphs_with_polish_characters(tmp_path):
    source = SAMPLES / "notatka.txt"

    result = execute(ConversionRequest(source, ".docx", tmp_path))

    assert result == tmp_path / "notatka.docx"
    assert paragraphs(result) == source.read_text(encoding="utf-8").splitlines()
    assert "Zażółć gęślą jaźń – ZAŻÓŁĆ GĘŚLĄ JAŹŃ." in paragraphs(result)


def test_txt_to_docx_creates_real_word_document_not_renamed_text(tmp_path):
    result = execute(ConversionRequest(SAMPLES / "notatka.txt", ".docx", tmp_path))

    assert zipfile.is_zipfile(result)
    assert "word/document.xml" in zipfile.ZipFile(result).namelist()


def test_txt_with_bom_and_windows_line_endings(tmp_path):
    source = tmp_path / "bom.txt"
    source.write_bytes("Pierwszy\r\n\r\nTrzeci – ąę\r\n".encode("utf-8-sig"))

    result = execute(ConversionRequest(source, ".docx", tmp_path))

    assert paragraphs(result) == ["Pierwszy", "", "Trzeci – ąę"]


@pytest.mark.parametrize(
    "content, message",
    [
        (b"", "pusty"),
        (b"  \r\n\t\r\n", "pusty"),
        ("Zażółć".encode("cp1250"), "UTF-8"),
        (b"tekst\x00binarny", "znaki sterujące"),
    ],
    ids=["empty-file", "only-whitespace", "not-utf8", "control-characters"],
)
def test_invalid_txt_gives_controlled_error_and_no_output(tmp_path, content, message):
    source = tmp_path / "zly.txt"
    source.write_bytes(content)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with pytest.raises(InvalidInputError, match=message):
        execute(ConversionRequest(source, ".docx", output_dir))
    assert list(output_dir.iterdir()) == []


def test_existing_docx_gets_safe_name(tmp_path):
    existing = tmp_path / "notatka.docx"
    existing.write_bytes(b"keep me")

    result = execute(ConversionRequest(SAMPLES / "notatka.txt", ".docx", tmp_path))

    assert result.name == "notatka (1).docx"
    assert existing.read_bytes() == b"keep me"


def test_missing_python_docx_gives_dependency_error(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "docx", None)  # makes "import docx" fail

    with pytest.raises(MissingDependencyError, match="python-docx") as error:
        execute(ConversionRequest(SAMPLES / "notatka.txt", ".docx", tmp_path))
    assert "pip install -r requirements.txt" in error.value.hint
    assert list(tmp_path.iterdir()) == []


def test_docx_to_txt_keeps_paragraph_order_and_polish_characters(tmp_path):
    source = SAMPLES / "dokument.docx"

    result = execute(ConversionRequest(source, ".txt", tmp_path))

    assert result == tmp_path / "dokument.txt"
    assert result.read_text(encoding="utf-8").splitlines() == paragraphs(source)
    assert "Raport z konwersji – zażółć gęślą jaźń" in result.read_text(encoding="utf-8")


def test_docx_to_txt_writes_tables_in_document_order(tmp_path):
    source = tmp_path / "tabela.docx"
    document = docx.Document()
    document.add_paragraph("Przed tabelą")
    table = document.add_table(rows=2, cols=2)
    for row, values in zip(table.rows, [["imię", "miasto"], ["Łukasz", "Łódź"]]):
        for cell, value in zip(row.cells, values):
            cell.text = value
    document.add_paragraph("Po tabeli")
    document.save(source)

    result = execute(ConversionRequest(source, ".txt", tmp_path))

    assert result.read_text(encoding="utf-8").splitlines() == [
        "Przed tabelą",
        "imię\tmiasto",
        "Łukasz\tŁódź",
        "Po tabeli",
    ]


def test_txt_docx_txt_round_trip_gives_same_lines(tmp_path):
    docx_dir, txt_dir = tmp_path / "docx", tmp_path / "txt"
    docx_dir.mkdir()
    txt_dir.mkdir()

    docx_file = execute(ConversionRequest(SAMPLES / "notatka.txt", ".docx", docx_dir))
    txt_file = execute(ConversionRequest(docx_file, ".txt", txt_dir))

    original = (SAMPLES / "notatka.txt").read_text(encoding="utf-8").splitlines()
    assert txt_file.read_text(encoding="utf-8").splitlines() == original


@pytest.mark.parametrize(
    "content",
    [b"to nie jest dokument", None],
    ids=["not-a-zip", "truncated-docx"],
)
def test_broken_docx_to_txt_gives_controlled_error_and_no_output(tmp_path, content):
    source = SAMPLES / "uszkodzony.docx" if content is None else tmp_path / "zly.docx"
    if content is not None:
        source.write_bytes(content)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with pytest.raises(InvalidInputError, match="nie jest poprawnym dokumentem DOCX"):
        execute(ConversionRequest(source, ".txt", output_dir))
    assert list(output_dir.iterdir()) == []
