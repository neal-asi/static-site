from htmlnode import HTMLNode

class ParentNode(HTMLNode):
    def __init__(self, tag: str, children: list['HTMLNode'], props: dict[str, str] | None = None):
        super().__init__(tag=tag, value=None, children=children, props=props)

    def to_html(self) -> str:
        if self.tag is None or self.tag == "":
            raise ValueError("No tag provided for ParentNode")

        if self.children is None or len(self.children) == 0:
            raise ValueError("No children provided for ParentNode")

        return f"<{self.tag}{self.props_to_html()}>{''.join(child.to_html() for child in self.children)}</{self.tag}>"



