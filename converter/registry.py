"""Converter registry, request validation and the shared error model.

Every conversion direction is a plain function ``(source, target) -> None``
registered with the ``@converter`` decorator. The GUI and the CLI only talk
to this module, so adding a new format pair never requires changing them.
"""
import logging
import os
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

Converter = Callable[[Path, Path], None]
REGISTRY: dict[tuple[str, str], Converter] = {}


class ConversionError(Exception):
    """Error shown to the user: what went wrong (message) and what to do (hint)."""

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return f"{self.message}\n{self.hint}" if self.hint else self.message


class InvalidInputError(ConversionError):
    """Input file is missing, unreadable or has invalid content."""


class UnsupportedConversionError(ConversionError):
    """The requested format pair is not in the registry."""


class OutputError(ConversionError):
    """The result cannot be written."""


class MissingDependencyError(ConversionError):
    """A required library or external tool is not installed."""


def converter(source: str, target: str):
    """Decorator registering a single conversion direction, e.g. ('.csv', '.json')."""

    def register(func: Converter) -> Converter:
        REGISTRY[(source.lower(), target.lower())] = func
        return func

    return register


def available_targets(source: Path) -> list[str]:
    """Target formats available for the given file, based on its extension."""
    extension = source.suffix.lower()
    return sorted(target for (src, target) in REGISTRY if src == extension)


def supported_pairs() -> list[tuple[str, str]]:
    return sorted(REGISTRY)


def is_writable(directory: Path) -> bool:
    try:
        with tempfile.TemporaryFile(dir=directory):
            return True
    except OSError:
        return False


def unique_path(path: Path) -> Path:
    """Return 'name (1).ext', 'name (2).ext', ... - the first one that does not exist."""
    number = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
        if not candidate.exists():
            return candidate
        number += 1


@dataclass(frozen=True)
class ConversionRequest:
    source: Path | None
    target_format: str
    output_dir: Path | None
    overwrite: bool = False

    @property
    def key(self) -> tuple[str, str]:
        return (self.source.suffix.lower(), self.target_format.lower())

    @property
    def default_target(self) -> Path:
        """Output path before resolving a name conflict."""
        return self.output_dir / f"{self.source.stem}{self.target_format.lower()}"

    def target_path(self) -> Path:
        """Final output path: overwrite the existing file or pick a safe free name."""
        target = self.default_target
        if self.overwrite or not target.exists():
            return target
        return unique_path(target)

    def validate(self) -> None:
        if self.source is None:
            raise InvalidInputError("Nie wybrano pliku wejściowego.", "Wskaż plik do konwersji.")
        if not self.source.is_file():
            raise InvalidInputError(
                f"Nie znaleziono pliku: {self.source}",
                "Sprawdź ścieżkę albo wybierz plik ponownie.",
            )
        if not self.target_format:
            raise UnsupportedConversionError(
                "Nie wybrano formatu docelowego.", "Wybierz format z listy."
            )
        if self.key not in REGISTRY:
            targets = available_targets(self.source)
            hint = (
                f"Dostępne formaty dla tego pliku: {', '.join(targets)}."
                if targets
                else "Ten typ pliku nie jest obsługiwany - zobacz tabelę formatów w README."
            )
            raise UnsupportedConversionError(
                f"Nieobsługiwana konwersja: {self.key[0]} -> {self.key[1]}", hint
            )
        if self.output_dir is None:
            raise OutputError("Nie wybrano katalogu docelowego.", "Wskaż katalog zapisu.")
        if not self.output_dir.is_dir():
            raise OutputError(
                f"Nie znaleziono katalogu: {self.output_dir}",
                "Wybierz istniejący katalog albo go utwórz.",
            )
        if not is_writable(self.output_dir):
            raise OutputError(
                f"Brak uprawnień do zapisu w katalogu: {self.output_dir}",
                "Wybierz inny katalog zapisu.",
            )


def execute(request: ConversionRequest) -> Path:
    """Validate the request, run the converter and return the path of the result.

    The converter writes to a temporary file which replaces the target only
    after success, so a failed conversion never leaves a broken or
    half-overwritten file behind.
    """
    request.validate()
    target = request.target_path()
    temp = target.with_name(f"~{target.stem}.tmp{target.suffix}")
    func = REGISTRY[request.key]

    log.info("Start: %s -> %s", request.source, target)
    started = time.perf_counter()
    try:
        func(request.source, temp)
        os.replace(temp, target)
    except ConversionError as error:
        log.error("Failed: %s (%s)", request.source, error.message)
        raise
    except OSError as error:
        log.exception("I/O error: %s", request.source)
        raise OutputError(
            f"Błąd dostępu do pliku: {error}",
            "Sprawdź, czy plik nie jest otwarty w innym programie i czy masz uprawnienia.",
        ) from error
    except Exception:
        log.exception("Unexpected error: %s", request.source)
        raise
    finally:
        temp.unlink(missing_ok=True)

    log.info("Done in %.2f s: %s", time.perf_counter() - started, target)
    return target
