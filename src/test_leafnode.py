import unittest
from leafnode import LeafNode

class TestLeafNode(unittest.TestCase):
    def test_to_html_with_tag_and_value(self):
        node = LeafNode(tag="p", value="Hello, World!", props={"class": "text"})
        expected_html = '<p class="text">Hello, World!</p>'
        self.assertEqual(node.to_html(), expected_html)

    def test_to_html_without_props(self):
        node = LeafNode(tag="b", value="bold")
        self.assertEqual(node.to_html(), "<b>bold</b>")

    def test_to_html_with_multiple_props(self):
        node = LeafNode(
            tag="a",
            value="link",
            props={"href": "https://example.com", "target": "_blank"},
        )
        self.assertEqual(
            node.to_html(),
            '<a href="https://example.com" target="_blank">link</a>',
        )

    def test_to_html_with_no_tag_returns_raw_value(self):
        node = LeafNode(tag=None, value="just text")
        self.assertEqual(node.to_html(), "just text")

    def test_to_html_with_no_tag_and_no_value_raises(self):
        node = LeafNode(tag=None, value=None)
        with self.assertRaises(ValueError):
            node.to_html()

    def test_to_html_with_empty_value_renders_empty_element(self):
        node = LeafNode(tag="p", value="")
        self.assertEqual(node.to_html(), "<p></p>")

    def test_to_html_with_none_value_raises(self):
        node = LeafNode(tag="p", value=None)
        with self.assertRaises(ValueError):
            node.to_html()

    def test_to_html_void_element_with_props(self):
        node = LeafNode(tag="img", value="", props={"src": "y.png", "alt": "alt text"})
        self.assertEqual(node.to_html(), '<img src="y.png" alt="alt text" />')

    def test_to_html_void_element_without_props(self):
        node = LeafNode(tag="br", value="")
        self.assertEqual(node.to_html(), "<br />")

    def test_to_html_void_element_is_case_insensitive(self):
        node = LeafNode(tag="IMG", value="", props={"src": "y.png"})
        self.assertEqual(node.to_html(), '<IMG src="y.png" />')

    def test_to_html_void_element_with_none_value_does_not_raise(self):
        node = LeafNode(tag="hr", value=None)
        self.assertEqual(node.to_html(), "<hr />")

    def test_to_html_void_element_ignores_value(self):
        node = LeafNode(tag="br", value="ignored")
        self.assertEqual(node.to_html(), "<br />")

    def test_to_html_anchor_is_not_void(self):
        node = LeafNode(tag="a", value="text", props={"href": "https://example.com"})
        self.assertEqual(node.to_html(), '<a href="https://example.com">text</a>')

    def test_repr(self):
        node = LeafNode(tag="span", value="Sample", props={"style": "color:red;"})
        expected_repr = "LeafNode(tag=span, value=Sample, props={'style': 'color:red;'})"
        self.assertEqual(repr(node), expected_repr)


if __name__ == "__main__":
    unittest.main()
