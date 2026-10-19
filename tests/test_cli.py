from pathlib import Path

from converter.__main__ import main

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_cli_creates_missing_output_dir(tmp_path):
    output_dir = tmp_path / "new" / "output"

    exit_code = main([str(SAMPLES / "osoby.csv"), "json", "-o", str(output_dir)])

    assert exit_code == 0
    assert (output_dir / "osoby.json").is_file()


def test_cli_returns_error_code_for_broken_input(tmp_path):
    exit_code = main([str(SAMPLES / "uszkodzony.json"), "csv", "-o", str(tmp_path)])

    assert exit_code == 1
    assert list(tmp_path.iterdir()) == []
