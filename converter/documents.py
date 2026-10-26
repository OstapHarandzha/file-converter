"""Group B - text documents: TXT -> DOCX (python-docx).

Semantics (also described in README):
* Input encoding: UTF-8 (with or without BOM); an empty file is an error.
* Every line of the text becomes one paragraph, in the same order;
  an empty line becomes an empty paragraph. No formatting is added.
"""
from pathlib import Path

from .data import read_utf8
from .registry import InvalidInputError, MissingDependencyError, converter


def load_docx():
    """Import python-docx only when needed, so a missing library gives a clear error."""
    try:
        import docx
    except ImportError as error:
        raise MissingDependencyError(
            "Brak biblioteki python-docx potrzebnej do obsługi plików DOCX.",
            "Zainstaluj zależności: pip install -r requirements.txt",
        ) from error
    return docx


@converter(".txt", ".docx")
def txt_to_docx(source: Path, target: Path) -> None:
    text = read_utf8(source)
    if not text.strip():
        raise InvalidInputError("Plik TXT jest pusty.", "Wybierz plik zawierający tekst.")

    document = load_docx().Document()
    try:
        for line in text.splitlines():
            document.add_paragraph(line)
    except ValueError as error:  # python-docx rejects NULL bytes and control characters
        raise InvalidInputError(
            "Plik TXT zawiera znaki sterujące, których nie można zapisać w DOCX.",
            "Sprawdź, czy to na pewno plik tekstowy, i usuń z niego znaki sterujące.",
        ) from error
    document.save(target)
