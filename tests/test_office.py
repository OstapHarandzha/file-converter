import subprocess
from pathlib import Path

import pytest

from converter import ConversionError, ConversionRequest, MissingDependencyError, execute, office

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def libreoffice_installed() -> bool:
    try:
        office.find_libreoffice()
        return True
    except MissingDependencyError:
        return False


needs_libreoffice = pytest.mark.skipif(not libreoffice_installed(), reason="LibreOffice is not installed")


@pytest.fixture
def fake_libreoffice(tmp_path, monkeypatch):
    """Replace the real program with a fake one; returns the list of recorded calls."""
    program = tmp_path / "soffice.com"
    program.write_text("fake")
    monkeypatch.setenv("LIBREOFFICE_PATH", str(program))
    calls = []
    behaviour = {"returncode": 0, "creates_output": True, "raises": None}

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if behaviour["raises"]:
            raise behaviour["raises"]
        if behaviour["creates_output"]:
            outdir = Path(command[command.index("--outdir") + 1])
            (outdir / f"{Path(command[-1]).stem}.pdf").write_bytes(b"%PDF-fake")
        return subprocess.CompletedProcess(command, behaviour["returncode"], stdout="", stderr="tool message")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls, behaviour


def test_libreoffice_is_called_safely_with_argument_list_and_timeout(tmp_path, fake_libreoffice):
    calls, _ = fake_libreoffice
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", output_dir))

    command, kwargs = calls[0]
    assert isinstance(command, list)
    assert command[0].endswith("soffice.com")
    assert ["--convert-to", "pdf"] == command[command.index("--convert-to"):][:2]
    assert "--headless" in command
    assert kwargs.get("shell", False) is False
    assert kwargs["timeout"] == office.TIMEOUT_SECONDS
    assert result == output_dir / "dokument.pdf"
    assert result.read_bytes() == b"%PDF-fake"


@pytest.mark.parametrize(
    "returncode, creates_output, raises, message",
    [
        (1, False, None, r"kod 1\): tool message"),
        (0, False, None, "nie utworzył pliku"),
        (None, False, subprocess.TimeoutExpired("soffice", 120), "120 s"),
        (None, False, OSError("not a program"), "Nie udało się uruchomić"),
    ],
    ids=["non-zero-exit-code", "exit-0-but-no-output", "timeout", "cannot-start"],
)
def test_failed_libreoffice_run_gives_controlled_error_and_no_output(
    tmp_path, fake_libreoffice, returncode, creates_output, raises, message
):
    _, behaviour = fake_libreoffice
    behaviour.update(returncode=returncode, creates_output=creates_output, raises=raises)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with pytest.raises(ConversionError, match=message):
        execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", output_dir))
    assert list(output_dir.iterdir()) == []


def test_existing_pdf_gets_safe_name(tmp_path, fake_libreoffice):
    existing = tmp_path / "dokument.pdf"
    existing.write_bytes(b"keep me")

    result = execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", tmp_path))

    assert result.name == "dokument (1).pdf"
    assert existing.read_bytes() == b"keep me"


def test_wrong_libreoffice_path_gives_dependency_error(tmp_path, monkeypatch):
    monkeypatch.setenv("LIBREOFFICE_PATH", str(tmp_path / "missing" / "soffice.com"))

    with pytest.raises(MissingDependencyError, match="LIBREOFFICE_PATH"):
        execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_libreoffice_not_installed_gives_install_hint(tmp_path, monkeypatch):
    monkeypatch.delenv("LIBREOFFICE_PATH", raising=False)
    monkeypatch.setattr(office.shutil, "which", lambda name: None)
    monkeypatch.setattr(office, "STANDARD_PATHS", [])

    with pytest.raises(MissingDependencyError, match="Nie znaleziono programu LibreOffice") as error:
        execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", tmp_path))
    assert "libreoffice.org" in error.value.hint


@needs_libreoffice
def test_real_docx_to_pdf_creates_pdf_file(tmp_path):
    result = execute(ConversionRequest(SAMPLES / "dokument.docx", ".pdf", tmp_path))

    assert result == tmp_path / "dokument.pdf"
    assert result.read_bytes().startswith(b"%PDF")


@needs_libreoffice
def test_real_broken_docx_gives_controlled_error(tmp_path):
    with pytest.raises(ConversionError, match="LibreOffice"):
        execute(ConversionRequest(SAMPLES / "uszkodzony.docx", ".pdf", tmp_path))
    assert list(tmp_path.iterdir()) == []
