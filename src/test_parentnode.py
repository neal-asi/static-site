import unittest

from leafnode import LeafNode
from parentnode import ParentNode

class TestParentNode(unittest.TestCase):
    def test_to_html_with_leaf_children(self):
        parent = ParentNode(
            tag="div",
            children=[
                LeafNode(tag="span", value="one", props={"class": "child1"}),
                LeafNode(tag="span", value="two", props={"class": "child2"}),
            ],
            props={"id": "parent"},
        )
        expected_html = '<div id="parent"><span class="child1">one</span><span class="child2">two</span></div>'
        self.assertEqual(parent.to_html(), expected_html)

    def test_to_html_without_props(self):
        parent = ParentNode(tag="p", children=[LeafNode(tag="b", value="bold")])
        self.assertEqual(parent.to_html(), "<p><b>bold</b></p>")

    def test_to_html_with_raw_text_child(self):
        parent = ParentNode(
            tag="p",
            children=[
                LeafNode(tag=None, value="plain "),
                LeafNode(tag="i", value="italic"),
            ],
        )
        self.assertEqual(parent.to_html(), "<p>plain <i>italic</i></p>")

    def test_to_html_with_nested_parents(self):
        grandchild = LeafNode(tag="b", value="deep")
        child = ParentNode(tag="span", children=[grandchild])
        parent = ParentNode(tag="div", children=[child])
        self.assertEqual(parent.to_html(), "<div><span><b>deep</b></span></div>")

    def test_to_html_with_many_levels(self):
        node = LeafNode(tag=None, value="bottom")
        for tag in ("em", "b", "p", "div"):
            node = ParentNode(tag=tag, children=[node])
        self.assertEqual(node.to_html(), "<div><p><b><em>bottom</em></b></p></div>")

    def test_to_html_with_mixed_children(self):
        parent = ParentNode(
            tag="ul",
            children=[
                LeafNode(tag="li", value="first"),
                ParentNode(tag="li", children=[LeafNode(tag="b", value="second")]),
            ],
        )
        self.assertEqual(parent.to_html(), "<ul><li>first</li><li><b>second</b></li></ul>")

    def test_to_html_with_multiple_props(self):
        parent = ParentNode(
            tag="a",
            children=[LeafNode(tag=None, value="link")],
            props={"href": "https://example.com", "target": "_blank"},
        )
        self.assertEqual(
            parent.to_html(),
            '<a href="https://example.com" target="_blank">link</a>',
        )

    def test_to_html_with_empty_children_raises(self):
        parent = ParentNode(tag="div", children=[], props={"id": "parent"})
        with self.assertRaises(ValueError):
            parent.to_html()

    def test_to_html_with_none_children_raises(self):
        parent = ParentNode(tag="div", children=None)
        with self.assertRaises(ValueError):
            parent.to_html()

    def test_to_html_with_no_tag_raises(self):
        parent = ParentNode(tag=None, children=[LeafNode(tag="b", value="bold")])
        with self.assertRaises(ValueError):
            parent.to_html()

    def test_to_html_with_empty_tag_raises(self):
        parent = ParentNode(tag="", children=[LeafNode(tag="b", value="bold")])
        with self.assertRaises(ValueError):
            parent.to_html()

    def test_to_html_propagates_child_error(self):
        parent = ParentNode(tag="div", children=[LeafNode(tag="b", value=None)])
        with self.assertRaises(ValueError):
            parent.to_html()

    def test_value_is_none(self):
        parent = ParentNode(tag="div", children=[LeafNode(tag="b", value="bold")])
        self.assertIsNone(parent.value)


if __name__ == "__main__":
    unittest.main()
