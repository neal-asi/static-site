import os
import sys

from node_utils import generate_pages_recursive
from static_utils import copy_static_to_destination

# Resolve against the project root so the script works from any working directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "template.html")


def main(base_path: str = "/"):
    copy_static_to_destination(STATIC_DIR, DOCS_DIR)

    generate_pages_recursive(
        dir_path_content=os.path.join(PROJECT_ROOT, "content"),
        template_path=TEMPLATE_PATH,
        dest_path=DOCS_DIR,
        base_path=base_path,
    )


if __name__ == "__main__":
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/"
    main(base_path)
