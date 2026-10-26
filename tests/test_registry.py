from pathlib import Path

import pytest

from converter import (
    ConversionRequest,
    InvalidInputError,
    OutputError,
    UnsupportedConversionError,
    available_targets,
    execute,
)

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_available_targets_depend_on_extension():
    assert available_targets(Path("a.csv")) == [".json"]
    assert available_targets(Path("A.JSON")) == [".csv"]
    assert available_targets(Path("notatka.txt")) == [".docx"]
    assert available_targets(Path("a.xyz")) == []
    assert available_targets(Path("no_extension")) == []


def test_validate_accepts_correct_request(tmp_path):
    ConversionRequest(SAMPLES / "osoby.csv", ".json", tmp_path).validate()


@pytest.mark.parametrize(
    "source, target_format, output_dir, error",
    [
        (None, ".json", "existing", InvalidInputError),
        ("missing.csv", ".json", "existing", InvalidInputError),
        ("osoby.csv", "", "existing", UnsupportedConversionError),
        ("osoby.csv", ".pdf", "existing", UnsupportedConversionError),
        ("osoby.csv", ".json", None, OutputError),
        ("osoby.csv", ".json", "missing", OutputError),
    ],
    ids=["no-source", "missing-file", "no-format", "unsupported-pair", "no-output-dir", "missing-output-dir"],
)
def test_validate_rejects_invalid_requests(tmp_path, source, target_format, output_dir, error):
    output_dirs = {"existing": tmp_path, "missing": tmp_path / "missing", None: None}
    request = ConversionRequest(
        source=SAMPLES / source if source else None,
        target_format=target_format,
        output_dir=output_dirs[output_dir],
    )
    with pytest.raises(error):
        request.validate()


def test_existing_target_gets_safe_name(tmp_path):
    existing = tmp_path / "osoby.json"
    existing.write_text("keep me", encoding="utf-8")

    first = execute(ConversionRequest(SAMPLES / "osoby.csv", ".json", tmp_path))
    second = execute(ConversionRequest(SAMPLES / "osoby.csv", ".json", tmp_path))

    assert first.name == "osoby (1).json"
    assert second.name == "osoby (2).json"
    assert existing.read_text(encoding="utf-8") == "keep me"


def test_overwrite_replaces_existing_target(tmp_path):
    existing = tmp_path / "osoby.json"
    existing.write_text("old", encoding="utf-8")

    result = execute(ConversionRequest(SAMPLES / "osoby.csv", ".json", tmp_path, overwrite=True))

    assert result == existing
    assert "Łódź" in existing.read_text(encoding="utf-8")
