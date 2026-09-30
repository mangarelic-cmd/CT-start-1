#!/usr/bin/env python3
"""Fetch a hash-pinned public release into a new directory; never run its code."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 96 * 1024 * 1024


def extract_checked(archive, destination, expected_sha256):
    if destination.exists():
        raise ValueError('Destination must not exist; choose a new empty location')
    if archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError('Archive exceeds configured size limit')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('Public archive SHA-256 does not match the pinned release')
    with zipfile.ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) > 2000 or sum(e.file_size for e in entries) > MAX_EXPANDED:
            raise ValueError('Expanded archive exceeds configured limits')
        names = set()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            if (not entry.filename or path.is_absolute() or '..' in path.parts
                    or '\\' in entry.filename or ':' in entry.filename
                    or stat.S_ISLNK(mode) or path in names):
                raise ValueError('Unsafe or duplicate ZIP member: ' + entry.filename)
            if not (stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError('Unsupported ZIP member type')
            names.add(path)
        # Validate all members before writing. Partial extraction remains confined
        # to the caller's newly created destination if a filesystem error occurs.
        destination.mkdir(parents=True, exist_ok=False)
        for entry in entries:
            target = destination / entry.filename
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(entry) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
    return len(entries)


def main():
    sources = json.loads((ROOT / 'PUBLIC_RELEASES.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', choices=sorted(sources))
    parser.add_argument('destination', type=Path)
    parser.add_argument('--archive', type=Path, help='Use an already downloaded archive; still verify its hash')
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('Destination already exists')
    release = sources[args.release]
    with tempfile.TemporaryDirectory(prefix='ct-public-download-') as temporary:
        archive = args.archive
        if archive is None:
            archive = Path(temporary) / 'release.zip'
            request = urllib.request.Request(release['archive_url'], headers={'User-Agent': 'CT-public-reproducibility/1'})
            with urllib.request.urlopen(request, timeout=180) as source, archive.open('xb') as output:
                total = 0
                while block := source.read(1024 * 1024):
                    total += len(block)
                    if total > MAX_ARCHIVE:
                        raise ValueError('Download exceeds configured size limit')
                    output.write(block)
        count = extract_checked(archive, args.destination, release['sha256'])
    print(json.dumps({'release': args.release, 'sha256': release['sha256'],
                      'members_extracted': count, 'destination': str(args.destination),
                      'execution': 'not run'}, indent=2))


if __name__ == '__main__':
    main()
