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
