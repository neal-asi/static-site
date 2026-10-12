import contextlib
import io
import os
import tempfile
import unittest

from blocktypes import BlockType

from node_utils import (
    block_to_block_type,
    extract_title,
    generate_page,
    markdown_to_html_node,
    extract_markdown_images,
    extract_markdown_links,
    split_nodes_delimiter,
    split_nodes_image,
    split_nodes_link,
    markdown_to_blocks,
    text_to_textnodes,
)
from textnode import TextNode, TextType


class TestSplitNodesDelimiter(unittest.TestCase):
    def test_delimiter_mid_string(self):
        node = TextNode("This is `code` here", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("code", TextType.CODE),
                TextNode(" here", TextType.TEXT),
            ],
        )

    def test_whole_string_delimited_drops_empties(self):
        node = TextNode("`code`", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("code", TextType.CODE)],
        )

    def test_delimiter_at_start(self):
        node = TextNode("`code` trailing", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("code", TextType.CODE), TextNode(" trailing", TextType.TEXT)],
        )

    def test_delimiter_at_end(self):
        node = TextNode("leading `code`", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("leading ", TextType.TEXT), TextNode("code", TextType.CODE)],
        )

    def test_adjacent_delimiters(self):
        node = TextNode("`a``b`", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("a", TextType.CODE), TextNode("b", TextType.CODE)],
        )

    def test_multiple_pairs(self):
        node = TextNode("a `one` b `two` c", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [
                TextNode("a ", TextType.TEXT),
                TextNode("one", TextType.CODE),
                TextNode(" b ", TextType.TEXT),
                TextNode("two", TextType.CODE),
                TextNode(" c", TextType.TEXT),
            ],
        )

    def test_multi_character_delimiter(self):
        node = TextNode("**bold** and **more**", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "**", TextType.BOLD),
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("more", TextType.BOLD),
            ],
        )

    def test_italic_delimiter(self):
        node = TextNode("an _italic_ word", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "_", TextType.ITALIC),
            [
                TextNode("an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word", TextType.TEXT),
            ],
        )

    def test_no_delimiter_returns_node_unchanged(self):
        node = TextNode("plain text", TextType.TEXT)
        self.assertListEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("plain text", TextType.TEXT)],
        )

    def test_non_text_node_passes_through_untouched(self):
        node = TextNode("already bold", TextType.BOLD)
        result = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertListEqual(result, [node])
        self.assertIs(result[0], node)

    def test_non_text_node_keeps_url(self):
        node = TextNode("boot.dev", TextType.LINK, "https://www.boot.dev")
        result = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(result[0].url, "https://www.boot.dev")

    def test_mixed_list_of_nodes(self):
        nodes = [
            TextNode("has `code`", TextType.TEXT),
            TextNode("already bold", TextType.BOLD),
            TextNode("plain", TextType.TEXT),
        ]
        self.assertListEqual(
            split_nodes_delimiter(nodes, "`", TextType.CODE),
            [
                TextNode("has ", TextType.TEXT),
                TextNode("code", TextType.CODE),
                TextNode("already bold", TextType.BOLD),
                TextNode("plain", TextType.TEXT),
            ],
        )

    def test_empty_input_list(self):
        self.assertListEqual(split_nodes_delimiter([], "`", TextType.CODE), [])

    def test_unmatched_delimiter_raises(self):
        node = TextNode("un`matched", TextType.TEXT)
        with self.assertRaises(ValueError):
            split_nodes_delimiter([node], "`", TextType.CODE)

    def test_unmatched_delimiter_in_later_node_raises(self):
        nodes = [TextNode("fine", TextType.TEXT), TextNode("bad `one", TextType.TEXT)]
        with self.assertRaises(ValueError):
            split_nodes_delimiter(nodes, "`", TextType.CODE)

    def test_chained_calls_for_multiple_types(self):
        nodes = [TextNode("**bold** and `code`", TextType.TEXT)]
        nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
        nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
        self.assertListEqual(
            nodes,
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("code", TextType.CODE),
            ],
        )

    def test_does_not_mutate_input_list(self):
        nodes = [TextNode("a `b` c", TextType.TEXT)]
        split_nodes_delimiter(nodes, "`", TextType.CODE)
        self.assertListEqual(nodes, [TextNode("a `b` c", TextType.TEXT)])


class TestExtractMarkdownImages(unittest.TestCase):
    def test_single_image(self):
        self.assertListEqual(
            extract_markdown_images("text ![alt](https://i.imgur.com/a.png) more"),
            [("alt", "https://i.imgur.com/a.png")],
        )

    def test_returns_tuples_not_lists(self):
        result = extract_markdown_images("![alt](a.png)")
        self.assertIsInstance(result[0], tuple)

    def test_multiple_images(self):
        self.assertListEqual(
            extract_markdown_images("![one](a.png) and ![two](b.png)"),
            [("one", "a.png"), ("two", "b.png")],
        )

    def test_adjacent_images(self):
        self.assertListEqual(
            extract_markdown_images("![a](u.png)![b](v.png)"),
            [("a", "u.png"), ("b", "v.png")],
        )

    def test_image_at_start_of_string(self):
        self.assertListEqual(
            extract_markdown_images("![alt](a.png) trailing"),
            [("alt", "a.png")],
        )

    def test_empty_alt_text(self):
        self.assertListEqual(extract_markdown_images("![](a.png)"), [("", "a.png")])

    def test_empty_url(self):
        self.assertListEqual(extract_markdown_images("![alt]()"), [("alt", "")])

    def test_ignores_plain_links(self):
        self.assertListEqual(extract_markdown_images("[boot](https://boot.dev)"), [])

    def test_no_markdown_returns_empty(self):
        self.assertListEqual(extract_markdown_images("just some text"), [])

    def test_empty_string_returns_empty(self):
        self.assertListEqual(extract_markdown_images(""), [])


class TestExtractMarkdownLinks(unittest.TestCase):
    def test_single_link(self):
        self.assertListEqual(
            extract_markdown_links("text [boot](https://boot.dev) more"),
            [("boot", "https://boot.dev")],
        )

    def test_returns_tuples_not_lists(self):
        result = extract_markdown_links("[boot](https://boot.dev)")
        self.assertIsInstance(result[0], tuple)

    def test_link_at_start_of_string(self):
        self.assertListEqual(
            extract_markdown_links("[boot](https://boot.dev)"),
            [("boot", "https://boot.dev")],
        )

    def test_adjacent_links(self):
        self.assertListEqual(
            extract_markdown_links("[a](u)[b](v)"),
            [("a", "u"), ("b", "v")],
        )

    def test_adjacent_links_after_leading_character(self):
        self.assertListEqual(
            extract_markdown_links("x[a](u)[b](v)"),
            [("a", "u"), ("b", "v")],
        )

    def test_multiple_links(self):
        self.assertListEqual(
            extract_markdown_links("[one](a.com) and [two](b.com)"),
            [("one", "a.com"), ("two", "b.com")],
        )

    def test_empty_link_text(self):
        self.assertListEqual(extract_markdown_links("[](a.com)"), [("", "a.com")])

    def test_empty_url(self):
        self.assertListEqual(extract_markdown_links("[text]()"), [("text", "")])

    def test_ignores_images(self):
        self.assertListEqual(extract_markdown_links("![alt](https://i.png)"), [])

    def test_separates_links_from_images(self):
        text = "an ![img](i.png) and a [link](l.com)"
        self.assertListEqual(extract_markdown_links(text), [("link", "l.com")])
        self.assertListEqual(extract_markdown_images(text), [("img", "i.png")])

    def test_image_immediately_followed_by_link(self):
        self.assertListEqual(
            extract_markdown_links("![img](i.png)[link](l.com)"),
            [("link", "l.com")],
        )

    def test_no_markdown_returns_empty(self):
        self.assertListEqual(extract_markdown_links("just some text"), [])

    def test_empty_string_returns_empty(self):
        self.assertListEqual(extract_markdown_links(""), [])


class TestSplitNodesImage(unittest.TestCase):
    def test_image_mid_string(self):
        node = TextNode("text ![alt](a.png) more", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]),
            [
                TextNode("text ", TextType.TEXT),
                TextNode("alt", TextType.IMAGE, "a.png"),
                TextNode(" more", TextType.TEXT),
            ],
        )

    def test_image_is_whole_string(self):
        node = TextNode("![alt](a.png)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]), [TextNode("alt", TextType.IMAGE, "a.png")]
        )

    def test_image_at_start(self):
        node = TextNode("![alt](a.png) trailing", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]),
            [TextNode("alt", TextType.IMAGE, "a.png"), TextNode(" trailing", TextType.TEXT)],
        )

    def test_image_at_end(self):
        node = TextNode("leading ![alt](a.png)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]),
            [TextNode("leading ", TextType.TEXT), TextNode("alt", TextType.IMAGE, "a.png")],
        )

    def test_multiple_images(self):
        node = TextNode("![a](u.png) mid ![b](v.png)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]),
            [
                TextNode("a", TextType.IMAGE, "u.png"),
                TextNode(" mid ", TextType.TEXT),
                TextNode("b", TextType.IMAGE, "v.png"),
            ],
        )

    def test_adjacent_images_produce_no_empty_nodes(self):
        node = TextNode("![a](u.png)![b](v.png)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_image([node]),
            [TextNode("a", TextType.IMAGE, "u.png"), TextNode("b", TextType.IMAGE, "v.png")],
        )

    def test_empty_alt_and_url(self):
        node = TextNode("![]()", TextType.TEXT)
        self.assertListEqual(split_nodes_image([node]), [TextNode("", TextType.IMAGE, "")])

    def test_no_images_returns_node_unchanged(self):
        node = TextNode("plain text", TextType.TEXT)
        self.assertListEqual(split_nodes_image([node]), [node])

    def test_plain_link_is_not_an_image(self):
        node = TextNode("a [link](l.com) here", TextType.TEXT)
        self.assertListEqual(split_nodes_image([node]), [node])

    def test_non_text_node_passes_through_untouched(self):
        node = TextNode("already bold", TextType.BOLD)
        result = split_nodes_image([node])
        self.assertListEqual(result, [node])
        self.assertIs(result[0], node)

    def test_multiple_input_nodes(self):
        nodes = [TextNode("![a](u.png)", TextType.TEXT), TextNode("plain", TextType.TEXT)]
        self.assertListEqual(
            split_nodes_image(nodes),
            [TextNode("a", TextType.IMAGE, "u.png"), TextNode("plain", TextType.TEXT)],
        )

    def test_empty_input_list(self):
        self.assertListEqual(split_nodes_image([]), [])

    def test_does_not_mutate_input_list(self):
        nodes = [TextNode("![a](u.png)", TextType.TEXT)]
        split_nodes_image(nodes)
        self.assertListEqual(nodes, [TextNode("![a](u.png)", TextType.TEXT)])


class TestSplitNodesLink(unittest.TestCase):
    def test_link_mid_string(self):
        node = TextNode("text [boot](b.dev) more", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [
                TextNode("text ", TextType.TEXT),
                TextNode("boot", TextType.LINK, "b.dev"),
                TextNode(" more", TextType.TEXT),
            ],
        )

    def test_link_at_start_of_string(self):
        node = TextNode("[boot](b.dev) trailing", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [TextNode("boot", TextType.LINK, "b.dev"), TextNode(" trailing", TextType.TEXT)],
        )

    def test_adjacent_links_produce_no_empty_nodes(self):
        node = TextNode("[a](u)[b](v)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [TextNode("a", TextType.LINK, "u"), TextNode("b", TextType.LINK, "v")],
        )

    def test_multiple_links(self):
        node = TextNode("[a](u) mid [b](v)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [
                TextNode("a", TextType.LINK, "u"),
                TextNode(" mid ", TextType.TEXT),
                TextNode("b", TextType.LINK, "v"),
            ],
        )

    def test_image_is_not_split_as_a_link(self):
        node = TextNode("![alt](a.png)", TextType.TEXT)
        self.assertListEqual(split_nodes_link([node]), [node])

    def test_does_not_match_inside_an_image(self):
        # Regression: find() used to locate "[a](u)" inside "![a](u)",
        # stranding the "!" and leaving the real link unparsed.
        node = TextNode("![a](u) [a](u)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [TextNode("![a](u) ", TextType.TEXT), TextNode("a", TextType.LINK, "u")],
        )

    def test_does_not_match_inside_an_image_with_repeats(self):
        node = TextNode("![a](u) [a](u) [a](u)", TextType.TEXT)
        self.assertListEqual(
            split_nodes_link([node]),
            [
                TextNode("![a](u) ", TextType.TEXT),
                TextNode("a", TextType.LINK, "u"),
                TextNode(" ", TextType.TEXT),
                TextNode("a", TextType.LINK, "u"),
            ],
        )

    def test_empty_link_text_and_url(self):
        node = TextNode("[]()", TextType.TEXT)
        self.assertListEqual(split_nodes_link([node]), [TextNode("", TextType.LINK, "")])

    def test_no_links_returns_node_unchanged(self):
        node = TextNode("plain text", TextType.TEXT)
        self.assertListEqual(split_nodes_link([node]), [node])

    def test_non_text_node_passes_through_untouched(self):
        node = TextNode("already bold", TextType.BOLD)
        result = split_nodes_link([node])
        self.assertListEqual(result, [node])
        self.assertIs(result[0], node)

    def test_empty_input_list(self):
        self.assertListEqual(split_nodes_link([]), [])


class TestSplitImageAndLinkTogether(unittest.TestCase):
    def test_order_does_not_matter(self):
        text = "![a](u) [a](u)"
        image_first = split_nodes_link(split_nodes_image([TextNode(text, TextType.TEXT)]))
        link_first = split_nodes_image(split_nodes_link([TextNode(text, TextType.TEXT)]))
        self.assertListEqual(image_first, link_first)
        self.assertListEqual(
            image_first,
            [
                TextNode("a", TextType.IMAGE, "u"),
                TextNode(" ", TextType.TEXT),
                TextNode("a", TextType.LINK, "u"),
            ],
        )

    def test_mixed_markdown(self):
        text = "start ![img](i.png) mid [link](l.com) end"
        nodes = split_nodes_link(split_nodes_image([TextNode(text, TextType.TEXT)]))
        self.assertListEqual(
            nodes,
            [
                TextNode("start ", TextType.TEXT),
                TextNode("img", TextType.IMAGE, "i.png"),
                TextNode(" mid ", TextType.TEXT),
                TextNode("link", TextType.LINK, "l.com"),
                TextNode(" end", TextType.TEXT),
            ],
        )

    def test_combined_with_delimiter_split(self):
        text = "`code` and ![img](i.png) and [link](l.com)"
        nodes = split_nodes_delimiter([TextNode(text, TextType.TEXT)], "`", TextType.CODE)
        nodes = split_nodes_link(split_nodes_image(nodes))
        self.assertListEqual(
            nodes,
            [
                TextNode("code", TextType.CODE),
                TextNode(" and ", TextType.TEXT),
                TextNode("img", TextType.IMAGE, "i.png"),
                TextNode(" and ", TextType.TEXT),
                TextNode("link", TextType.LINK, "l.com"),
            ],
        )


class TestTextToTextNodes(unittest.TestCase):
    def test_all_types_together(self):
        text = (
            "This is **text** with an _italic_ word and a `code block` "
            "and an ![image](i.png) and a [link](l.com)"
        )
        self.assertListEqual(
            text_to_textnodes(text),
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("text", TextType.BOLD),
                TextNode(" with an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word and a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" and an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "i.png"),
                TextNode(" and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "l.com"),
            ],
        )

    def test_plain_text(self):
        self.assertListEqual(
            text_to_textnodes("just words"), [TextNode("just words", TextType.TEXT)]
        )

    def test_bold_only(self):
        self.assertListEqual(
            text_to_textnodes("**bold**"), [TextNode("bold", TextType.BOLD)]
        )

    def test_italic_only(self):
        self.assertListEqual(
            text_to_textnodes("_italic_"), [TextNode("italic", TextType.ITALIC)]
        )

    def test_code_only(self):
        self.assertListEqual(
            text_to_textnodes("`code`"), [TextNode("code", TextType.CODE)]
        )

    def test_image_only(self):
        self.assertListEqual(
            text_to_textnodes("![alt](a.png)"), [TextNode("alt", TextType.IMAGE, "a.png")]
        )

    def test_link_only(self):
        self.assertListEqual(
            text_to_textnodes("[boot](b.dev)"), [TextNode("boot", TextType.LINK, "b.dev")]
        )

    def test_bold_before_italic(self):
        # "**" must be consumed before "*" or bold would split as two italics.
        self.assertListEqual(
            text_to_textnodes("**bold** and _italic_"),
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
            ],
        )

    def test_italic_before_bold_in_source_order(self):
        self.assertListEqual(
            text_to_textnodes("_italic_ and **bold**"),
            [
                TextNode("italic", TextType.ITALIC),
                TextNode(" and ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
            ],
        )

    def test_multiple_of_same_type(self):
        self.assertListEqual(
            text_to_textnodes("**a** and **b**"),
            [
                TextNode("a", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("b", TextType.BOLD),
            ],
        )

    def test_image_and_link_together(self):
        self.assertListEqual(
            text_to_textnodes("![img](i.png) then [link](l.com)"),
            [
                TextNode("img", TextType.IMAGE, "i.png"),
                TextNode(" then ", TextType.TEXT),
                TextNode("link", TextType.LINK, "l.com"),
            ],
        )

    def test_url_containing_delimiter_is_not_split(self):
        # Links are extracted before the delimiter passes, so "*" inside a
        # URL never reaches split_nodes_delimiter.
        self.assertListEqual(
            text_to_textnodes("[link](https://x.com/a_b_c)"),
            [TextNode("link", TextType.LINK, "https://x.com/a_b_c")],
        )

    def test_image_url_containing_delimiter_is_not_split(self):
        self.assertListEqual(
            text_to_textnodes("![alt](https://x.com/a_b_c.png)"),
            [TextNode("alt", TextType.IMAGE, "https://x.com/a_b_c.png")],
        )

    def test_markup_at_both_ends(self):
        self.assertListEqual(
            text_to_textnodes("**a** mid `b`"),
            [
                TextNode("a", TextType.BOLD),
                TextNode(" mid ", TextType.TEXT),
                TextNode("b", TextType.CODE),
            ],
        )

    def test_empty_string_returns_single_empty_text_node(self):
        # Documents current behaviour; an empty input is not special-cased.
        self.assertListEqual(text_to_textnodes(""), [TextNode("", TextType.TEXT)])

    def test_unmatched_delimiter_raises(self):
        with self.assertRaises(ValueError):
            text_to_textnodes("a lone _ underscore")


class TestMarkdownToBlocks(unittest.TestCase):
    def test_heading_paragraph_and_list(self):
        markdown = "# Heading\n\nA paragraph\n\n- item 1\n- item 2"
        self.assertListEqual(
            markdown_to_blocks(markdown),
            ["# Heading", "A paragraph", "- item 1\n- item 2"],
        )

    def test_single_block(self):
        self.assertListEqual(markdown_to_blocks("just one paragraph"), ["just one paragraph"])

    def test_multiline_block_keeps_internal_newlines(self):
        self.assertListEqual(
            markdown_to_blocks("line one\nline two"), ["line one\nline two"]
        )

    def test_three_newlines_collapse_to_one_split(self):
        self.assertListEqual(markdown_to_blocks("a\n\n\nb"), ["a", "b"])

    def test_many_blank_lines_collapse(self):
        self.assertListEqual(markdown_to_blocks("a\n\n\n\n\n\nb"), ["a", "b"])

    def test_leading_and_trailing_blank_lines_dropped(self):
        self.assertListEqual(markdown_to_blocks("\n\na\n\nb\n\n"), ["a", "b"])

    def test_blocks_are_stripped(self):
        self.assertListEqual(
            markdown_to_blocks("  # Heading  \n\n  para  "), ["# Heading", "para"]
        )

    def test_empty_string(self):
        self.assertListEqual(markdown_to_blocks(""), [])

    def test_whitespace_only_document(self):
        self.assertListEqual(markdown_to_blocks("   \n\n   "), [])

    def test_whitespace_only_separator_does_not_split(self):
        # Documents current behaviour: only a literal "\n\n" separates blocks,
        # so a blank line containing spaces keeps the text as one block.
        self.assertListEqual(markdown_to_blocks("a\n   \nb"), ["a\n   \nb"])

    def test_crlf_does_not_split(self):
        # Documents current behaviour: Windows line endings are not recognised.
        self.assertListEqual(markdown_to_blocks("a\r\n\r\nb"), ["a\r\n\r\nb"])

    def test_block_strip_dedents_only_the_first_line(self):
        # Documents current behaviour: .strip() removes the block's leading
        # indentation, so later lines keep theirs.
        self.assertListEqual(
            markdown_to_blocks("- a\n- b\n\n  - nested\n  - more"),
            ["- a\n- b", "- nested\n  - more"],
        )


class TestBlockToBlockType(unittest.TestCase):
    def test_heading_one_hash(self):
        self.assertEqual(block_to_block_type("# Heading"), BlockType.HEADING)

    def test_heading_six_hashes(self):
        self.assertEqual(block_to_block_type("###### Heading"), BlockType.HEADING)

    def test_seven_hashes_is_paragraph(self):
        self.assertEqual(block_to_block_type("####### Nope"), BlockType.PARAGRAPH)

    def test_hash_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("#hashtag"), BlockType.PARAGRAPH)

    def test_shebang_is_paragraph(self):
        self.assertEqual(block_to_block_type("#!/bin/bash"), BlockType.PARAGRAPH)

    def test_code_block(self):
        self.assertEqual(block_to_block_type("```\ncode\n```"), BlockType.CODE)

    def test_code_block_with_language_tag(self):
        self.assertEqual(block_to_block_type("```python\ncode\n```"), BlockType.CODE)

    def test_single_line_code_block(self):
        self.assertEqual(block_to_block_type("```code```"), BlockType.CODE)

    def test_code_block_containing_other_markers(self):
        # Code is checked first, so quote/list markers inside a fence stay code.
        self.assertEqual(
            block_to_block_type("```\n> quote\n- item\n```"), BlockType.CODE
        )

    def test_unclosed_fence_is_paragraph(self):
        self.assertEqual(block_to_block_type("```\ncode"), BlockType.PARAGRAPH)

    def test_quote_single_line(self):
        self.assertEqual(block_to_block_type("> quote"), BlockType.QUOTE)

    def test_quote_every_line(self):
        self.assertEqual(
            block_to_block_type("> line one\n> line two"), BlockType.QUOTE
        )

    def test_quote_without_space_is_still_quote(self):
        self.assertEqual(block_to_block_type(">no space"), BlockType.QUOTE)

    def test_partial_quote_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("> quote\nnot a quote"), BlockType.PARAGRAPH
        )

    def test_unordered_list_single_item(self):
        self.assertEqual(block_to_block_type("- item"), BlockType.UNORDERED_LIST)

    def test_unordered_list_every_line(self):
        self.assertEqual(block_to_block_type("- a\n- b\n- c"), BlockType.UNORDERED_LIST)

    def test_partial_unordered_list_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("- item\nnot an item"), BlockType.PARAGRAPH
        )

    def test_dash_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("-nospace"), BlockType.PARAGRAPH)

    def test_ordered_list_single_item(self):
        self.assertEqual(block_to_block_type("1. one"), BlockType.ORDERED_LIST)

    def test_ordered_list_increments(self):
        self.assertEqual(
            block_to_block_type("1. a\n2. b\n3. c"), BlockType.ORDERED_LIST
        )

    def test_ordered_list_must_start_at_one(self):
        self.assertEqual(block_to_block_type("5. five"), BlockType.PARAGRAPH)

    def test_ordered_list_must_increment_by_one(self):
        self.assertEqual(block_to_block_type("1. a\n3. c"), BlockType.PARAGRAPH)

    def test_partial_ordered_list_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("1. a\nnot a list"), BlockType.PARAGRAPH
        )

    def test_number_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("1.\nfoo"), BlockType.PARAGRAPH)

    def test_plain_paragraph(self):
        self.assertEqual(block_to_block_type("just some words"), BlockType.PARAGRAPH)

    def test_multiline_paragraph(self):
        self.assertEqual(
            block_to_block_type("line one\nline two"), BlockType.PARAGRAPH
        )


class TestBlocksWithTypes(unittest.TestCase):
    def test_document_blocks_and_types(self):
        markdown = (
            "# Title\n\n"
            "A paragraph of text.\n\n"
            "```\ncode here\n```\n\n"
            "> a quote\n> continued\n\n"
            "- one\n- two\n\n"
            "1. first\n2. second"
        )
        blocks = markdown_to_blocks(markdown)
        self.assertListEqual(
            [block_to_block_type(b) for b in blocks],
            [
                BlockType.HEADING,
                BlockType.PARAGRAPH,
                BlockType.CODE,
                BlockType.QUOTE,
                BlockType.UNORDERED_LIST,
                BlockType.ORDERED_LIST,
            ],
        )


class TestMarkdownToHtmlNode(unittest.TestCase):
    def test_wraps_everything_in_a_div(self):
        node = markdown_to_html_node("hello")
        self.assertEqual(node.tag, "div")
        self.assertEqual(node.to_html(), "<div><p>hello</p></div>")

    def test_paragraph_with_inline_markdown(self):
        md = "A **bold** and _italic_ and `code` word"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><p>A <b>bold</b> and <i>italic</i> and <code>code</code> word</p></div>",
        )

    def test_paragraph_soft_wrap_becomes_a_space(self):
        md = "line one\nline two"
        self.assertEqual(
            markdown_to_html_node(md).to_html(), "<div><p>line one line two</p></div>"
        )

    def test_multiple_paragraphs(self):
        md = "first para\n\nsecond para"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><p>first para</p><p>second para</p></div>",
        )

    def test_paragraph_with_link_and_image(self):
        md = "see ![alt](a.png) and [boot](b.dev)"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            '<div><p>see <img src="a.png" alt="alt" /> and <a href="b.dev">boot</a></p></div>',
        )

    def test_all_heading_levels(self):
        for level in range(1, 7):
            md = f"{'#' * level} Heading"
            self.assertEqual(
                markdown_to_html_node(md).to_html(),
                f"<div><h{level}>Heading</h{level}></div>",
            )

    def test_heading_with_inline_markdown(self):
        self.assertEqual(
            markdown_to_html_node("## A **bold** heading").to_html(),
            "<div><h2>A <b>bold</b> heading</h2></div>",
        )

    def test_code_block(self):
        md = "```\nprint()\n```"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><pre><code>print()\n</code></pre></div>",
        )

    def test_code_block_with_language_tag(self):
        md = '```python\nprint("hi")\n```'
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            '<div><pre><code>print("hi")\n</code></pre></div>',
        )

    def test_single_line_code_block(self):
        self.assertEqual(
            markdown_to_html_node("```inline```").to_html(),
            "<div><pre><code>inline</code></pre></div>",
        )

    def test_code_block_does_not_parse_inline_markdown(self):
        md = "```\n**not bold** and _not italic_\n```"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><pre><code>**not bold** and _not italic_\n</code></pre></div>",
        )

    def test_quote_single_line(self):
        self.assertEqual(
            markdown_to_html_node("> a quote").to_html(),
            "<div><blockquote>a quote</blockquote></div>",
        )

    def test_quote_joins_lines_and_strips_markers(self):
        md = "> line one\n> line two"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><blockquote>line one line two</blockquote></div>",
        )

    def test_quote_with_inline_markdown(self):
        self.assertEqual(
            markdown_to_html_node("> a **bold** quote").to_html(),
            "<div><blockquote>a <b>bold</b> quote</blockquote></div>",
        )

    def test_unordered_list(self):
        md = "- one\n- two"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ul><li>one</li><li>two</li></ul></div>",
        )

    def test_unordered_list_with_inline_markdown(self):
        md = "- plain\n- **bold**"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ul><li>plain</li><li><b>bold</b></li></ul></div>",
        )

    def test_ordered_list(self):
        md = "1. first\n2. second\n3. third"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ol><li>first</li><li>second</li><li>third</li></ol></div>",
        )

    def test_ordered_list_double_digit_items(self):
        md = "\n".join(f"{i}. item {i}" for i in range(1, 12))
        html = markdown_to_html_node(md).to_html()
        self.assertIn("<li>item 10</li>", html)
        self.assertIn("<li>item 11</li>", html)

    def test_full_document(self):
        md = (
            "# Title\n\n"
            "A paragraph with **bold**\n\n"
            "```\ncode\n```\n\n"
            "> quoted\n\n"
            "- one\n- two\n\n"
            "1. first\n2. second"
        )
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div>"
            "<h1>Title</h1>"
            "<p>A paragraph with <b>bold</b></p>"
            "<pre><code>code\n</code></pre>"
            "<blockquote>quoted</blockquote>"
            "<ul><li>one</li><li>two</li></ul>"
            "<ol><li>first</li><li>second</li></ol>"
            "</div>",
        )

    def test_blank_lines_between_blocks_are_ignored(self):
        md = "# Title\n\n\n\npara"
        self.assertEqual(
            markdown_to_html_node(md).to_html(), "<div><h1>Title</h1><p>para</p></div>"
        )

    def test_empty_markdown_produces_childless_div(self):
        # Documents current behaviour: no blocks means no children, and
        # ParentNode.to_html() rejects a childless node.
        node = markdown_to_html_node("")
        self.assertEqual(node.tag, "div")
        self.assertListEqual(node.children, [])
        with self.assertRaises(ValueError):
            node.to_html()


class TestExtractTitle(unittest.TestCase):
    def test_single_h1(self):
        self.assertEqual(extract_title("# Hello"), "Hello")

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(extract_title("#   Hello   "), "Hello")

    def test_h1_after_other_blocks(self):
        md = "A paragraph\n\n# The Title\n\nmore text"
        self.assertEqual(extract_title(md), "The Title")

    def test_first_h1_wins(self):
        md = "# First\n\n# Second"
        self.assertEqual(extract_title(md), "First")

    def test_h1_with_inline_markdown_is_returned_raw(self):
        self.assertEqual(extract_title("# A **bold** title"), "A **bold** title")

    def test_no_h1_raises(self):
        with self.assertRaises(ValueError):
            extract_title("just a paragraph")

    def test_h2_alone_raises(self):
        with self.assertRaises(ValueError):
            extract_title("## Not a title")

    def test_hash_without_space_raises(self):
        with self.assertRaises(ValueError):
            extract_title("#hashtag")

    def test_h1_inside_code_fence_is_not_a_title(self):
        with self.assertRaises(ValueError):
            extract_title("```\n# not a title\n```")

    def test_empty_markdown_raises(self):
        with self.assertRaises(ValueError):
            extract_title("")


class TestGeneratePage(unittest.TestCase):
    TEMPLATE = (
        "<html><head><title>{{ Title }}</title></head>"
        "<body><article>{{ Content }}</article></body></html>"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.template_path = os.path.join(self.tmp, "template.html")
        with open(self.template_path, "w") as handle:
            handle.write(self.TEMPLATE)

    def tearDown(self):
        self._tmp.cleanup()

    def write_markdown(self, markdown: str) -> str:
        path = os.path.join(self.tmp, "index.md")
        with open(path, "w") as handle:
            handle.write(markdown)
        return path

    def generate(self, markdown: str, dest_name: str = "index.html") -> tuple[str, str]:
        """Generate a page, returning (written html, captured log output)."""
        from_path = self.write_markdown(markdown)
        dest_path = os.path.join(self.tmp, "out", dest_name)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            generate_page(from_path, self.template_path, dest_path)
        with open(dest_path) as handle:
            return handle.read(), buffer.getvalue()

    def test_substitutes_title_and_content(self):
        html, _ = self.generate("# My Title\n\nA paragraph")
        self.assertEqual(
            html,
            "<html><head><title>My Title</title></head>"
            "<body><article><div><h1>My Title</h1><p>A paragraph</p></div></article></body></html>",
        )

    def test_leaves_no_placeholders_behind(self):
        html, _ = self.generate("# Title\n\nbody")
        self.assertNotIn("{{", html)
        self.assertNotIn("}}", html)

    def test_inline_markdown_is_rendered(self):
        html, _ = self.generate("# T\n\nA **bold** word and a [link](l.com)")
        self.assertIn("<b>bold</b>", html)
        self.assertIn('<a href="l.com">link</a>', html)

    def test_creates_missing_destination_directories(self):
        from_path = self.write_markdown("# T\n\nbody")
        dest_path = os.path.join(self.tmp, "deep", "deeper", "index.html")
        with contextlib.redirect_stdout(io.StringIO()):
            generate_page(from_path, self.template_path, dest_path)
        self.assertTrue(os.path.isfile(dest_path))

    def test_logs_the_paths(self):
        _, output = self.generate("# T\n\nbody")
        self.assertIn("Generating page from", output)
        self.assertIn(self.template_path, output)

    def test_markdown_without_h1_raises(self):
        from_path = self.write_markdown("just a paragraph")
        dest_path = os.path.join(self.tmp, "out", "index.html")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                generate_page(from_path, self.template_path, dest_path)

    def test_missing_source_raises(self):
        dest_path = os.path.join(self.tmp, "out", "index.html")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(FileNotFoundError):
                generate_page(
                    os.path.join(self.tmp, "nope.md"), self.template_path, dest_path
                )

    def test_missing_template_raises(self):
        from_path = self.write_markdown("# T\n\nbody")
        dest_path = os.path.join(self.tmp, "out", "index.html")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(FileNotFoundError):
                generate_page(
                    from_path, os.path.join(self.tmp, "nope.html"), dest_path
                )

    def test_overwrites_an_existing_page(self):
        self.generate("# First\n\nbody")
        html, _ = self.generate("# Second\n\nbody")
        self.assertIn("<title>Second</title>", html)
        self.assertNotIn("First", html)


if __name__ == "__main__":
    unittest.main()
