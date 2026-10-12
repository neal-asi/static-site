import unittest
from textnode import TextNode, TextType, text_node_to_html_node


class TestTextNode(unittest.TestCase):
    def test_eq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_url_none(self):
        node = TextNode("link that's none", TextType.LINK)
        self.assertIsNone(node.url)

    def test_url_value(self):
        node = TextNode("link with url", TextType.LINK, "https://www.example.com")
        self.assertEqual(node.url, "https://www.example.com")

    def test_repr(self):
        node = TextNode("This is a text node", TextType.ITALIC, "https://www.example.com")
        self.assertEqual(repr(node), "TextNode(This is a text node, TextType.ITALIC, https://www.example.com)")

    def test_text(self):
        node = TextNode("This is a text node", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, None)
        self.assertEqual(html_node.value, "This is a text node")

    def test_to_html_text(self):
        node = TextNode("raw text", TextType.TEXT)
        self.assertEqual(text_node_to_html_node(node).to_html(), "raw text")

    def test_to_html_bold(self):
        node = TextNode("bold text", TextType.BOLD)
        self.assertEqual(text_node_to_html_node(node).to_html(), "<b>bold text</b>")

    def test_to_html_italic(self):
        node = TextNode("italic text", TextType.ITALIC)
        self.assertEqual(text_node_to_html_node(node).to_html(), "<i>italic text</i>")

    def test_to_html_code(self):
        node = TextNode("print()", TextType.CODE)
        self.assertEqual(text_node_to_html_node(node).to_html(), "<code>print()</code>")

    def test_to_html_link(self):
        node = TextNode("boot.dev", TextType.LINK, "https://www.boot.dev")
        self.assertEqual(
            text_node_to_html_node(node).to_html(),
            '<a href="https://www.boot.dev">boot.dev</a>',
        )

    def test_to_html_image(self):
        node = TextNode("alt text", TextType.IMAGE, "https://www.boot.dev/y.png")
        self.assertEqual(
            text_node_to_html_node(node).to_html(),
            '<img src="https://www.boot.dev/y.png" alt="alt text" />',
        )

    def test_link_without_url_raises(self):
        node = TextNode("no url", TextType.LINK)
        with self.assertRaises(ValueError):
            text_node_to_html_node(node)

    def test_image_without_url_raises(self):
        node = TextNode("no url", TextType.IMAGE)
        with self.assertRaises(ValueError):
            text_node_to_html_node(node)


if __name__ == "__main__":
    unittest.main()
