"""Tests for HTML content cleaner."""

from src.fetching.content_cleaner import clean_html


class TestCleanHtml:
    """Tests for the clean_html function."""

    def test_removes_nav_elements(self) -> None:
        html = "<html><body><nav>Menu nav</nav><div>Content</div></body></html>"
        result = clean_html(html)
        assert "Menu nav" not in result
        assert "Content" in result

    def test_removes_footer_elements(self) -> None:
        html = "<html><body><div>Content</div><footer>Footer stuff</footer></body></html>"
        result = clean_html(html)
        assert "Footer stuff" not in result
        assert "Content" in result

    def test_removes_script_and_style(self) -> None:
        html = """
        <html><body>
        <script>var x = 1;</script>
        <style>.foo { color: red; }</style>
        <div>Real content</div>
        </body></html>
        """
        result = clean_html(html)
        assert "var x" not in result
        assert ".foo" not in result
        assert "Real content" in result

    def test_removes_elements_by_class(self) -> None:
        html = """
        <html><body>
        <div class="navigation">Nav content</div>
        <div class="sidebar-widget">Sidebar</div>
        <div class="menu-content">Menu items here</div>
        </body></html>
        """
        result = clean_html(html)
        assert "Nav content" not in result
        assert "Sidebar" not in result
        assert "Menu items here" in result

    def test_preserves_menu_content(self, sample_menu_html: str) -> None:
        result = clean_html(sample_menu_html)
        assert "Butter Chicken" in result
        assert "$17.99" in result
        assert "Samosa" in result
        # Nav and footer should be removed
        assert "Navigation here" not in result
        assert "Footer content" not in result

    def test_collapses_blank_lines(self) -> None:
        html = "<html><body><div>A</div><div></div><div></div><div></div><div>B</div></body></html>"
        result = clean_html(html)
        assert "\n\n\n" not in result

    def test_empty_input(self) -> None:
        result = clean_html("")
        assert result == ""
