"""Unit tests for pure helper functions in the Streamlit dashboard (US-014/017)."""

from streamlit_app import flag_emoji, format_number


class TestFlagEmoji:
    """Tests for the ISO2-to-flag-emoji converter."""

    def test_valid_iso2_produces_regional_indicator_pair(self):
        """Should convert a valid ISO2 code to its two regional indicator symbols."""
        result = flag_emoji("BR")
        assert result == "\U0001F1E7\U0001F1F7"

    def test_lowercase_iso2_is_normalized(self):
        """Should uppercase the code before conversion."""
        assert flag_emoji("br") == flag_emoji("BR")

    def test_empty_string_returns_empty(self):
        """Should return an empty string for missing/empty codes."""
        assert flag_emoji("") == ""

    def test_none_like_invalid_length_returns_empty(self):
        """Should return an empty string for codes that aren't exactly 2 letters."""
        assert flag_emoji("BRA") == ""
        assert flag_emoji("B") == ""

    def test_non_alpha_returns_empty(self):
        """Should return an empty string for non-alphabetic input."""
        assert flag_emoji("12") == ""


class TestFormatNumber:
    """Tests for the pt-BR style thousands-separator formatter."""

    def test_formats_with_dot_separator(self):
        """Should use '.' as the thousands separator instead of ','."""
        assert format_number(8063308369) == "8.063.308.369"

    def test_small_number_has_no_separator(self):
        """Should not add a separator for numbers under 1000."""
        assert format_number(250) == "250"

    def test_zero(self):
        """Should format zero as '0'."""
        assert format_number(0) == "0"
