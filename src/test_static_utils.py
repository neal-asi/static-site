import contextlib
import io
import os
import tempfile
import unittest

from static_utils import copy_static_to_destination


def copy_quietly(source_path: str, destination_path: str) -> str:
    """Run the copy, capturing its log output instead of printing it."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        copy_static_to_destination(source_path, destination_path)
    return buffer.getvalue()


def write(path: str, content: str = "x") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(content)


def relative_files(path: str) -> list[str]:
    found = []
    for root, _, files in os.walk(path):
        for name in files:
            found.append(os.path.relpath(os.path.join(root, name), path))
    return sorted(found)


class TestCopyStaticToDestination(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.source = os.path.join(self.tmp, "static")
        self.destination = os.path.join(self.tmp, "public")
        os.makedirs(self.source)

    def tearDown(self):
        self._tmp.cleanup()

    def test_copies_a_single_file(self):
        write(os.path.join(self.source, "index.css"))
        copy_quietly(self.source, self.destination)
        self.assertListEqual(relative_files(self.destination), ["index.css"])

    def test_copies_nested_directories(self):
        write(os.path.join(self.source, "images", "a.png"))
        write(os.path.join(self.source, "deep", "deeper", "b.txt"))
        copy_quietly(self.source, self.destination)
        self.assertListEqual(
            relative_files(self.destination),
            [os.path.join("deep", "deeper", "b.txt"), os.path.join("images", "a.png")],
        )

    def test_creates_destination_when_missing(self):
        write(os.path.join(self.source, "a.css"))
        self.assertFalse(os.path.exists(self.destination))
        copy_quietly(self.source, self.destination)
        self.assertTrue(os.path.isdir(self.destination))

    def test_removes_stale_destination_content(self):
        write(os.path.join(self.source, "new.css"))
        write(os.path.join(self.destination, "old.html"))
        write(os.path.join(self.destination, "stale", "deep", "old.txt"))
        copy_quietly(self.source, self.destination)
        self.assertListEqual(relative_files(self.destination), ["new.css"])

    def test_file_contents_are_preserved(self):
        write(os.path.join(self.source, "a.txt"), "hello world")
        copy_quietly(self.source, self.destination)
        with open(os.path.join(self.destination, "a.txt")) as handle:
            self.assertEqual(handle.read(), "hello world")

    def test_skips_ds_store(self):
        write(os.path.join(self.source, "index.css"))
        write(os.path.join(self.source, ".DS_Store"))
        write(os.path.join(self.source, "images", ".DS_Store"))
        write(os.path.join(self.source, "images", "a.png"))
        copy_quietly(self.source, self.destination)
        self.assertListEqual(
            relative_files(self.destination),
            [os.path.join("images", "a.png"), "index.css"],
        )

    def test_empty_source_yields_empty_destination(self):
        copy_quietly(self.source, self.destination)
        self.assertTrue(os.path.isdir(self.destination))
        self.assertListEqual(relative_files(self.destination), [])

    def test_missing_source_raises(self):
        with self.assertRaises(ValueError):
            copy_quietly(os.path.join(self.tmp, "nope"), self.destination)

    def test_missing_source_leaves_destination_untouched(self):
        write(os.path.join(self.destination, "keep.html"))
        with self.assertRaises(ValueError):
            copy_quietly(os.path.join(self.tmp, "nope"), self.destination)
        self.assertListEqual(relative_files(self.destination), ["keep.html"])

    def test_source_that_is_a_file_raises(self):
        not_a_dir = os.path.join(self.tmp, "file.txt")
        write(not_a_dir)
        with self.assertRaises(ValueError):
            copy_quietly(not_a_dir, self.destination)

    def test_logs_each_copied_file(self):
        write(os.path.join(self.source, "a.css"))
        write(os.path.join(self.source, "images", "b.png"))
        output = copy_quietly(self.source, self.destination)
        self.assertIn("copied a.css", output)
        self.assertIn(f"copied {os.path.join('images', 'b.png')}", output)

    def test_repeated_copies_are_idempotent(self):
        write(os.path.join(self.source, "a.css"))
        write(os.path.join(self.source, "images", "b.png"))
        copy_quietly(self.source, self.destination)
        first = relative_files(self.destination)
        copy_quietly(self.source, self.destination)
        self.assertListEqual(relative_files(self.destination), first)


if __name__ == "__main__":
    unittest.main()
