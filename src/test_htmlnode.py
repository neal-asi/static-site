import unittest
from textnode import TextNode, TextType

class TestHTMLNode(unittest.TestCase):
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
