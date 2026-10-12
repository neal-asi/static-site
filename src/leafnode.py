from htmlnode import HTMLNode, VOID_ELEMENTS

class LeafNode(HTMLNode):
    def __init__(self, tag: str, value: str, props: dict[str, str] | None = None):
        super().__init__(tag=tag, value=value, children=None, props=props)

    def to_html(self) -> str:
        if self.tag is None:
            if self.value is None:
                raise ValueError("No value provided for LeafNode")

            return self.value

        if self.tag.lower() in VOID_ELEMENTS:
            return f"<{self.tag}{self.props_to_html()} />"

        if self.value is None:
            raise ValueError("No value provided for LeafNode")

        return f"<{self.tag}{self.props_to_html()}>{self.value}</{self.tag}>"

    def __repr__(self) -> str:
        return f"LeafNode(tag={self.tag}, value={self.value}, props={self.props})"
