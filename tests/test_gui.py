import pytest

pytest.importorskip("tkinter")  # the GUI module needs Tkinter; skip on Python builds without it

from converter import supported_pairs  # noqa: E402
from converter.gui import help_text  # noqa: E402


def test_help_lists_every_supported_pair_once():
    text = help_text()

    assert f"Obsługiwane konwersje ({len(supported_pairs())}):" in text
    for source, target in supported_pairs():
        assert text.count(f"{source}  →  {target}") == 1
