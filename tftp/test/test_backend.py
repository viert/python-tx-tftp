'''
@author: shylent
'''
from tftp.backend import (FilesystemSynchronousBackend, FilesystemReader,
    FilesystemWriter, IReader, IWriter)
from tftp.errors import Unsupported, AccessViolation, FileNotFound, FileExists
from twisted.python.filepath import FilePath
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest
import shutil
import tempfile


class BackendSelection(unittest.TestCase):
    test_data = b"""line1
line2
line3
"""


    def setUp(self):
        self.temp_dir = FilePath(tempfile.mkdtemp()).asBytesMode()
        self.existing_file_name = self.temp_dir.descendant((b"dir", b"foo"))
        self.existing_file_name.parent().makedirs()
        self.existing_file_name.setContent(self.test_data)

    @inlineCallbacks
    def test_read_supported_by_default(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        reader = yield b.get_reader(b'dir/foo')
        self.assertTrue(IReader.providedBy(reader))

    @inlineCallbacks
    def test_write_supported_by_default(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        writer = yield b.get_writer(b'dir/bar')
        self.assertTrue(IWriter.providedBy(writer))

    def test_read_unsupported(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path, can_read=False)
        return self.assertFailure(b.get_reader(b'dir/foo'), Unsupported)

    def test_write_unsupported(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path, can_write=False)
        return self.assertFailure(b.get_writer(b'dir/bar'), Unsupported)

    def test_insecure_reader(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        return self.assertFailure(
            b.get_reader(b'../foo'), AccessViolation)

    def test_insecure_writer(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        return self.assertFailure(
            b.get_writer(b'../foo'), AccessViolation)

    @inlineCallbacks
    def test_read_ignores_leading_and_trailing_slashes(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        reader = yield b.get_reader(b'/dir/foo/')
        segments_from_root = reader.file_path.segmentsFrom(self.temp_dir)
        self.assertEqual([b"dir", b"foo"], segments_from_root)

    @inlineCallbacks
    def test_write_ignores_leading_and_trailing_slashes(self):
        b = FilesystemSynchronousBackend(self.temp_dir.path)
        writer = yield b.get_writer(b'/dir/bar/')
        segments_from_root = writer.file_path.segmentsFrom(self.temp_dir)
        self.assertEqual([b"dir", b"bar"], segments_from_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir.path)


class Reader(unittest.TestCase):
    test_data = b"""line1
line2
line3
"""

    def setUp(self):
        self.temp_dir = FilePath(tempfile.mkdtemp()).asBytesMode()
        self.existing_file_name = self.temp_dir.child(b'foo')
        with self.existing_file_name.open('w') as f:
            f.write(self.test_data)

    def test_file_not_found(self):
        self.assertRaises(FileNotFound, FilesystemReader, self.temp_dir.child(b'bar'))

    def test_read_existing_file(self):
        r = FilesystemReader(self.temp_dir.child(b'foo'))
        data = r.read(3)
        ostring = data
        while data:
            data = r.read(3)
            ostring += data
        self.assertEqual(r.read(3), b'')
        self.assertEqual(r.read(5), b'')
        self.assertEqual(r.read(7), b'')
        self.assertTrue(r.file_obj.closed,
                        b"The file has been exhausted and should be in the closed state")
        self.assertEqual(ostring, self.test_data)

    def test_size(self):
        r = FilesystemReader(self.temp_dir.child(b'foo'))
        self.assertEqual(len(self.test_data), r.size)

    def test_size_when_reader_finished(self):
        r = FilesystemReader(self.temp_dir.child(b'foo'))
        r.finish()
        self.assertTrue(r.size is None)

    def test_size_when_file_removed(self):
        # FilesystemReader.size uses fstat() to discover the file's size, so
        # the absence of the file does not matter.
        r = FilesystemReader(self.temp_dir.child(b'foo'))
        self.existing_file_name.remove()
        self.assertEqual(len(self.test_data), r.size)

    def test_cancel(self):
        r = FilesystemReader(self.temp_dir.child(b'foo'))
        r.read(3)
        r.finish()
        self.assertTrue(r.file_obj.closed,

            "The session has been finished, so the file object should be in the closed state")
        r.finish()

    def tearDown(self):
        self.temp_dir.remove()


class Writer(unittest.TestCase):
    test_data = b"""line1
line2
line3
"""

    def setUp(self):
        self.temp_dir = FilePath(tempfile.mkdtemp()).asBytesMode()
        self.existing_file_name = self.temp_dir.child(b'foo')
        self.existing_file_name.setContent(self.test_data)

    def test_write_existing_file(self):
        self.assertRaises(FileExists, FilesystemWriter, self.temp_dir.child(b'foo'))

    def test_write_to_non_existent_directory(self):
        new_directory = self.temp_dir.child(b"new")
        new_file = new_directory.child(b"baz")
        self.assertFalse(new_directory.exists())
        FilesystemWriter(new_file).finish()
        self.assertTrue(new_directory.exists())
        self.assertTrue(new_file.exists())

    def test_finished_write(self):
        w = FilesystemWriter(self.temp_dir.child(b'bar'))
        w.write(self.test_data)
        w.finish()
        with self.temp_dir.child(b'bar').open() as f:
            self.assertEqual(f.read(), self.test_data)

    def test_cancelled_write(self):
        w = FilesystemWriter(self.temp_dir.child(b'bar'))
        w.write(self.test_data)
        w.cancel()
        self.assertFalse(self.temp_dir.child(b'bar').exists(),
                    "If a write is cancelled, the file should not be left behind")

    def tearDown(self):
        self.temp_dir.remove()
