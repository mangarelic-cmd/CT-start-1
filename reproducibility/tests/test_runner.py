import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

runner = load('run')
download = load('download_release')

class RunnerTests(unittest.TestCase):
    def test_frozen_sources(self):
        self.assertEqual(runner.verify_sources(), 7)

    def test_memory_fixture_counts(self):
        source = ROOT / 'vendor/causal_memory_v2_1'
        self.assertEqual(len(json.loads((source / 'results.json').read_text())['ladder']), 10)
        self.assertEqual(len(json.loads((source / 'scaling.json').read_text())), 4)

    def test_manifest_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'source').write_text('mutated')
            (root / 'SOURCE_MANIFEST.json').write_text(json.dumps({'files':[
                {'path':'source','sha256':hashlib.sha256(b'original').hexdigest()}]}))
            with self.assertRaises(ValueError):
                runner.verify_sources(root)

    def test_alignment_is_scoped(self):
        result = runner.alignment()
        self.assertEqual(result['demos_executed'], 16)
        self.assertEqual(result['finite_configurations'], 248832)
        self.assertEqual(len(result['not_run']), 3)

    def test_boundary_fail_closed(self):
        with self.assertRaises(ValueError):
            runner.section('missing source', 'start', 'end')
        with self.assertRaises(ValueError):
            runner.section('start start end', 'start', 'end')

    def zip_case(self, name, wrong_hash=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'input.zip'
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr(name, 'payload')
            sha = '0' * 64 if wrong_hash else hashlib.sha256(archive.read_bytes()).hexdigest()
            destination = root / 'output'
            with self.assertRaises(ValueError):
                download.extract_checked(archive, destination, sha)
            self.assertFalse(destination.exists())

    def test_wrong_archive_hash(self):
        self.zip_case('safe.txt', wrong_hash=True)

    def test_path_traversal(self):
        for name in ('../escape.txt', '/absolute.txt', 'a\\escape.txt', 'C:/escape.txt'):
            with self.subTest(name=name):
                self.zip_case(name)

    def test_valid_extract_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'input.zip'
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr('nested/file.txt', 'payload')
            sha = hashlib.sha256(archive.read_bytes()).hexdigest()
            destination = root / 'output'
            self.assertEqual(download.extract_checked(archive, destination, sha), 1)
            self.assertEqual((destination / 'nested/file.txt').read_text(), 'payload')
            with self.assertRaises(ValueError):
                download.extract_checked(archive, destination, sha)

if __name__ == '__main__':
    unittest.main()
