import os
import shutil

# Filesystem noise that should never end up in the generated site.
SKIPPED_NAMES = frozenset({".DS_Store"})


def copy_static_to_destination(source_path: str, destination_path: str) -> None:
    """Replace everything under `destination_path` with the contents of `source_path`.

    This deletes the destination directory, so the source is validated first: a
    typo'd or missing source would otherwise wipe the destination and copy nothing.
    """
    if not os.path.isdir(source_path):
        raise ValueError(f"Source directory does not exist: {source_path}")

    shutil.rmtree(destination_path, ignore_errors=True)
    os.makedirs(destination_path, exist_ok=True)

    for root, _, files in os.walk(source_path):
        for name in files:
            if name in SKIPPED_NAMES:
                continue

            source_file_path = os.path.join(root, name)
            relative_path = os.path.relpath(source_file_path, source_path)
            destination_file_path = os.path.join(destination_path, relative_path)

            os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
            shutil.copy2(source_file_path, destination_file_path)
            print(f"copied {relative_path}")
