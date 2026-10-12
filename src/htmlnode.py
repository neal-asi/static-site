VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"})

class HTMLNode:
    def __init__(self, tag: str | None = None, value: str | None = None, children: list['HTMLNode'] | None = None, props: dict[str, str] | None = None):
        self.tag = tag
        self.value = value
        self.children = children if children is not None else []
        self.props = props if props is not None else {}


    def to_html(self):
        raise NotImplementedError()

    def props_to_html(self) -> str:
        if not self.props:
            return ""
        return " " + " ".join(f'{key}="{value}"' for key, value in self.props.items())

    def __repr__(self) -> str:
        return f"HTMLNode(tag={self.tag}, value={self.value}, children={self.children}, props={self.props})"



