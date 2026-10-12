import os

from node_utils import generate_pages_recursive
from static_utils import copy_static_to_destination

# Resolve against the project root so the script works from any working directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "template.html")


def main():
    copy_static_to_destination(STATIC_DIR, PUBLIC_DIR)

    generate_pages_recursive(
        dir_path_content=os.path.join(PROJECT_ROOT, "content"),
        template_path=TEMPLATE_PATH,
        dest_path=os.path.join(PUBLIC_DIR),
    )


if __name__ == "__main__":
    main()
