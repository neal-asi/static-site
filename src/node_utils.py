from blocktypes import BlockType
from htmlnode import HTMLNode
from leafnode import LeafNode
from parentnode import ParentNode
from textnode import TextNode, TextType, text_node_to_html_node
import os
import re

IMAGE_PATTERN = r"!\[([^\[\]]*)\]\(([^\(\)]*)\)"
LINK_PATTERN = r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)"


def split_nodes_delimiter(old_nodes: list[TextNode], delimiter: str, text_type: TextType) -> list[TextNode]:
    new_nodes: list[TextNode] = []

    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        if delimiter not in node.text:
            new_nodes.append(node)
            continue

        if node.text.count(delimiter) % 2 != 0:
            raise ValueError(f"Unmatched delimiter '{delimiter}' in text: {node.text}")

        parts = node.text.split(delimiter)
        for i, part in enumerate(parts):
            if not part:
                continue

            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))


    return new_nodes

def extract_markdown_images(text: str) -> list[tuple[str, str]]:
    return re.findall(IMAGE_PATTERN, text)


def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    return re.findall(LINK_PATTERN, text)


def _split_nodes_by_pattern(
    old_nodes: list[TextNode], pattern: str, text_type: TextType
) -> list[TextNode]:
    """Split TEXT nodes on `pattern`, whose groups are (text, url).

    Match positions come from the regex itself, so a pattern with a lookbehind
    (see LINK_PATTERN) cannot be re-matched at a position it deliberately excluded.
    """
    new_nodes: list[TextNode] = []

    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        matches = list(re.finditer(pattern, node.text))
        if not matches:
            new_nodes.append(node)
            continue

        last_index = 0
        for match in matches:
            if match.start() > last_index:
                new_nodes.append(
                    TextNode(node.text[last_index:match.start()], TextType.TEXT)
                )
            new_nodes.append(TextNode(match.group(1), text_type, match.group(2)))
            last_index = match.end()

        if last_index < len(node.text):
            new_nodes.append(TextNode(node.text[last_index:], TextType.TEXT))

    return new_nodes


def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
    return _split_nodes_by_pattern(old_nodes, IMAGE_PATTERN, TextType.IMAGE)


def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:
    return _split_nodes_by_pattern(old_nodes, LINK_PATTERN, TextType.LINK)

def text_to_textnodes(text: str) -> list[TextNode]:
    """Convert a string to a list of TextNodes, splitting on markdown syntax."""
    nodes: list[TextNode] = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes

def markdown_to_blocks(markdown: str) -> list[str]:
    """Convert a markdown string to a list of blocks, splitting on double newlines."""
    return [block.strip() for block in markdown.split("\n\n") if block.strip()]

def block_to_block_type(block: str) -> BlockType:
    """Determine the BlockType of a block.

    Quote and list blocks are defined by every line matching, not just the
    first, so those checks run over all lines. Code is tested first because a
    fenced block may legitimately contain lines starting with ">" or "- ".
    """
    lines = block.split("\n")

    if block.startswith("```") and block.endswith("```"):
        return BlockType.CODE

    if re.match(r"#{1,6} ", block):
        return BlockType.HEADING

    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    if all(line.startswith(f"{i}. ") for i, line in enumerate(lines, start=1)):
        return BlockType.ORDERED_LIST

    return BlockType.PARAGRAPH

def text_to_children(text: str) -> list[HTMLNode]:
    """Convert a string of inline markdown to a list of HTMLNodes."""
    return [text_node_to_html_node(node) for node in text_to_textnodes(text)]


def _heading_to_html_node(block: str) -> ParentNode:
    level = len(block) - len(block.lstrip("#"))
    return ParentNode(f"h{level}", text_to_children(block[level + 1:]))


def _code_to_html_node(block: str) -> ParentNode:
    """Build <pre><code>. Code content is literal, so inline markdown is not parsed."""
    inner = block[3:-3]
    if inner.startswith("\n"):
        inner = inner[1:]
    else:
        # Drop an opening language tag, e.g. ```python
        newline = inner.find("\n")
        if newline != -1:
            inner = inner[newline + 1:]
    return ParentNode("pre", [LeafNode("code", inner)])


def _quote_to_html_node(block: str) -> ParentNode:
    lines = [line.lstrip(">").strip() for line in block.split("\n")]
    return ParentNode("blockquote", text_to_children(" ".join(lines)))

def _unordered_list_to_html_node(block: str) -> ParentNode:
    items = [
        ParentNode("li", text_to_children(line[2:])) for line in block.split("\n")
    ]
    return ParentNode("ul", items)


def _ordered_list_to_html_node(block: str) -> ParentNode:
    items = [
        ParentNode("li", text_to_children(line[len(f"{i}. "):]))
        for i, line in enumerate(block.split("\n"), start=1)
    ]
    return ParentNode("ol", items)


def _paragraph_to_html_node(block: str) -> ParentNode:
    # Markdown soft-wraps: newlines inside a paragraph are just spaces.
    return ParentNode("p", text_to_children(" ".join(block.split("\n"))))


_BLOCK_BUILDERS = {
    BlockType.HEADING: _heading_to_html_node,
    BlockType.CODE: _code_to_html_node,
    BlockType.QUOTE: _quote_to_html_node,
    BlockType.UNORDERED_LIST: _unordered_list_to_html_node,
    BlockType.ORDERED_LIST: _ordered_list_to_html_node,
    BlockType.PARAGRAPH: _paragraph_to_html_node,
}


def markdown_to_html_node(markdown: str) -> ParentNode:
    """Convert a full markdown document to a single <div> HTMLNode."""
    children = [
        _BLOCK_BUILDERS[block_to_block_type(block)](block)
        for block in markdown_to_blocks(markdown)
    ]
    return ParentNode("div", children)

def extract_title(markdown: str) -> str:
    """Extract the h1 title from markdown content. If no h1 is found, throw exception. e.g. `# Title` returns `Title`."""
    blocks = markdown_to_blocks(markdown)
    for block in blocks:
        if block.startswith("# "):
            return block[2:].strip()
    raise ValueError("No h1 title found in markdown content.")

def generate_page(from_path: str, template_path: str, dest_path: str) -> None:
    """Render the markdown at `from_path` into `template_path` and write `dest_path`."""
    print(f"Generating page from {from_path} using template {template_path} to {dest_path}")

    with open(from_path, "r", encoding="utf-8") as f:
        markdown = f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html_string = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)

    page = template.replace("{{ Title }}", title).replace("{{ Content }}", html_string)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(page)

def generate_pages_recursive(dir_path_content, template_path, dest_path) -> None:
    """Recursively generate pages from markdown files in `dir_path_content` using `template_path` and write to `dest_path`."""
    for root, dirs, files in os.walk(dir_path_content):
        for file in files:
            if file.endswith(".md"):
                from_path = os.path.join(root, file)
                relative_path = os.path.relpath(from_path, dir_path_content)
                dest_file = os.path.splitext(relative_path)[0] + ".html"
                dest_file_path = os.path.join(dest_path, dest_file)

                generate_page(from_path, template_path, dest_file_path)
