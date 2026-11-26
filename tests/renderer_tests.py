import re
import unittest

import check50
import check50.renderer


def _collapse_whitespace(html):
    """Drop the template's indentation so assertions do not depend on it."""
    return re.sub(r"\s+", "", html)


def _output_panels(html):
    """The contents of the <samp> output panels, which should hold plain text."""
    return re.findall(r"<samp>(.*?)</samp>", html, flags=re.DOTALL)


def _render(cause):
    """Render a single failed check with the given cause and return the HTML."""
    result = {
        "name": "prints_hello",
        "description": "prints hello",
        "passed": False,
        "log": [],
        "cause": cause,
        "data": {},
        "dependency": None,
    }
    return check50.renderer.to_html("cs50/problems/test", [result], check50.__version__)


class TestHtmlRenderer(unittest.TestCase):
    """Test that the HTML log renders Missing/Mismatch payloads as plain text."""

    def test_missing_multiline_collection(self):
        """Test that a multi-line collection renders with line breaks, not escaped newlines."""
        missing = check50.Missing("hello", "line1\nline2\nline3\n")

        html = _render(missing.payload)
        item_panel, collection_panel = _output_panels(html)

        self.assertIn("line1<br/>line2<br/>line3<br/>", collection_panel)
        for panel in (item_panel, collection_panel):
            self.assertNotIn("\\n", panel)
            self.assertNotIn("&#39;", panel)
        # The missing item is shown as-is, without repr quotes
        self.assertEqual(_collapse_whitespace(item_panel), "hello")

    def test_mismatch_multiline_output(self):
        """Test that multi-line expected/actual output renders with line breaks."""
        mismatch = check50.Mismatch("hello\nworld", "hello")

        html = _render(mismatch.payload)
        expected_panel, actual_panel = _output_panels(html)

        self.assertIn("hello<br/>world", expected_panel)
        self.assertEqual(_collapse_whitespace(actual_panel), "hello")
        for panel in (expected_panel, actual_panel):
            self.assertNotIn("\\n", panel)
            self.assertNotIn("&#39;", panel)

    def test_mismatch_highlights_trailing_newline(self):
        """Test that the renderer still sees a real trailing newline and highlights it."""
        mismatch = check50.Mismatch("hello\n", "hello")

        html = _render(mismatch.payload)
        expected_panel, _ = _output_panels(html)

        # Only plain text lets the renderer spot the trailing special character
        self.assertRegex(expected_panel, r"hello<span [^>]*title='This is an invisible or trailing special character\.'>\\n</span>")

    def test_rationale_keeps_repr(self):
        """Test that the terminal-style rationale (with repr quotes) is still shown as the cause."""
        mismatch = check50.Mismatch("hello\n", "")

        html = _render(mismatch.payload)

        # Jinja escapes the quotes of the repr; the escaped newline is literal text here
        self.assertIn("expected:&nbsp;&#39;hello\\n&#39;", html)


if __name__ == "__main__":
    unittest.main()
