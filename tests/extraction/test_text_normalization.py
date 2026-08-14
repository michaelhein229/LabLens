import pytest

from lablens.extraction.text_normalization import normalize_text


def test_normalize_text_cleans_spacing_and_line_endings():
    raw_text = "  Experiment   24  \r\n\r\nHigh burst release observed.  \r\n"

    result = normalize_text(raw_text)

    assert result == "Experiment 24\n\nHigh burst release observed."


def test_normalize_text_collapses_excess_blank_lines():
    raw_text = "Formulation details\n\n\n\nRelease results"

    result = normalize_text(raw_text)

    assert result == "Formulation details\n\nRelease results"


def test_normalize_text_preserves_scientific_content():
    raw_text = "Experiment 24 used 2% PVA at 800 RPM and 10 mg/mL."

    result = normalize_text(raw_text)

    assert result == raw_text


@pytest.mark.parametrize("raw_text", ["", "   ", "\t\n\r\n"])
def test_normalize_text_returns_empty_string_for_blank_input(raw_text):
    assert normalize_text(raw_text) == ""


def test_normalize_text_does_not_modify_its_input():
    raw_text = "  PLGA Batch A\n\nObserved at 37°C.  "
    original_text = raw_text

    normalize_text(raw_text)

    assert raw_text == original_text
