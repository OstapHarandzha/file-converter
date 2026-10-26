"""Group C - office formats converted by LibreOffice in headless mode: DOCX -> PDF.

LibreOffice is an external program, so it is called safely:
* the command is a list of arguments (never shell=True) with a time limit;
* the exit code is checked and the output file must exist afterwards;
* a missing program or a failed start gives a controlled error with a hint.

Where the program is looked for, in order: the LIBREOFFICE_PATH environment
variable, 'soffice' / 'libreoffice' on PATH, the standard install folders.
LibreOffice runs with its own profile folder, so the conversion also works
while the user has LibreOffice open.
"""
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .registry import ConversionError, MissingDependencyError, converter

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 120
STANDARD_PATHS = [
    Path(r"C:\Program Files\LibreOffice\program\soffice.com"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.com"),
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    Path("/usr/bin/soffice"),
    Path("/usr/bin/libreoffice"),
]
PROFILE_DIR = Path(tempfile.gettempdir()) / "converter-libreoffice-profile"
INSTALL_HINT = (
    "Zainstaluj LibreOffice (https://www.libreoffice.org/download/) "
    "albo ustaw zmienną LIBREOFFICE_PATH na ścieżkę do programu soffice."
)


def find_libreoffice() -> Path:
    configured = os.environ.get("LIBREOFFICE_PATH")
    if configured:
        if Path(configured).is_file():
            return Path(configured)
        raise MissingDependencyError(
            f"Nie znaleziono LibreOffice pod ścieżką z LIBREOFFICE_PATH: {configured}",
            "Popraw zmienną LIBREOFFICE_PATH albo ją usuń, aby użyć domyślnej instalacji.",
        )
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return Path(found)
    for path in STANDARD_PATHS:
        if path.is_file():
            return path
    raise MissingDependencyError("Nie znaleziono programu LibreOffice potrzebnego do tej konwersji.", INSTALL_HINT)


def run_libreoffice(source: Path, target: Path) -> None:
    """Convert source into the format given by target's extension."""
    program = find_libreoffice()
    target_format = target.suffix.lstrip(".")
    with tempfile.TemporaryDirectory() as work_dir:
        command = [
            str(program),
            f"-env:UserInstallation={PROFILE_DIR.as_uri()}",
            "--headless",
            "--norestore",
            "--convert-to", target_format,
            "--outdir", work_dir,
            str(source),
        ]
        log.info("Running: %s", command)
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, errors="replace", timeout=TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired as error:
            raise ConversionError(
                f"LibreOffice nie zakończył konwersji w ciągu {TIMEOUT_SECONDS} s.",
                "Spróbuj ponownie; jeśli problem się powtarza, otwórz plik w LibreOffice i sprawdź go.",
            ) from error
        except OSError as error:
            raise ConversionError(
                f"Nie udało się uruchomić LibreOffice ({program}): {error}",
                "Sprawdź instalację LibreOffice i zmienną LIBREOFFICE_PATH.",
            ) from error

        output = (result.stderr + result.stdout).strip()
        log.info("LibreOffice exit code %s, output: %s", result.returncode, output)
        details = output.splitlines()[-1] if output else ""  # the last line holds the actual error
        if result.returncode != 0:
            raise ConversionError(
                f"LibreOffice zakończył pracę z błędem (kod {result.returncode}): {details}",
                "Sprawdź, czy plik nie jest uszkodzony - spróbuj otworzyć go w LibreOffice lub Wordzie.",
            )
        produced = Path(work_dir) / f"{source.stem}.{target_format}"
        if not produced.is_file():
            raise ConversionError(
                f"LibreOffice nie utworzył pliku wynikowego. {details}".strip(),
                "Sprawdź, czy plik nie jest uszkodzony - spróbuj otworzyć go w LibreOffice lub Wordzie.",
            )
        shutil.move(produced, target)


@converter(".docx", ".pdf")
def docx_to_pdf(source: Path, target: Path) -> None:
    run_libreoffice(source, target)
