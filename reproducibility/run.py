#!/usr/bin/env python3
"""Portable, explicitly scoped runner for the frozen public demo sources."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def verify_sources(root=ROOT):
    manifest = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
    for entry in manifest['files']:
        path = root / entry['path']
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Source manifest path escapes the bundle')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f"Source checksum mismatch: {entry['path']}")
    return len(manifest['files'])


def section(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Frozen alignment source boundaries have changed')
    return text[text.index(start):text.index(end)]


def alignment():
    path = ROOT / 'vendor/alignment_v7/build_alignment_v7_formal_and_demos.py'
    text = path.read_text()
    # Only the unchanged pure D65-D80/audit sections are evaluated. In particular,
    # never execute the original top-level /mnt/data directory deletion/build.
    namespace = {'itertools': itertools}
    for label, start, end in [
        ('D65-D80', 'def res(', '# Normalize base result list'),
        ('finite-audit', 'vals=(-1,0,1)', "(OUT/'DEMOS/COUNTERMODEL_AUDIT_V7.json').write_text"),
    ]:
        exec(compile(section(text, start, end), str(path) + '::' + label, 'exec'), namespace)
    demos, audit = namespace['new'], namespace['audit']
    if len(demos) != 16 or not all(row['passed'] for row in demos):
        raise AssertionError('One or more of the 16 newly implemented demos failed')
    expected = json.loads((ROOT / 'vendor/alignment_v7/COUNTERMODEL_AUDIT_V7.json').read_text())
    if audit != expected:
        raise AssertionError('Fresh finite audit differs from the published audit')
    return {
        'status': 'PASS_SCOPED', 'demos_executed': 16, 'demos_passed': 16,
        'finite_configurations': audit['state_space']['total_configurations'],
        'finite_audit_matches_published': True,
        'full_guard': audit['full_guard'],
        'not_run': ['64 inherited V6 demos', 'full V6-to-V7 build', 'AC73 solver audit'],
    }


def command(argv, cwd, timeout=900):
    print('Running: ' + ' '.join(argv), file=sys.stderr, flush=True)
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(argv)}\n"
                           + result.stdout + result.stderr)
    return result.stdout


def memory(full=False):
    versions = {name: importlib.metadata.version(name) for name in ('numpy', 'brotli', 'lz4')}
    if not shutil.which('zstd'):
        raise RuntimeError('Missing Zstandard CLI: install zstd (tested with 1.5.7)')
    versions['zstd_cli'] = subprocess.check_output(['zstd', '--version'], text=True).strip()
    source = ROOT / 'vendor/causal_memory_v2_1'
    expected = json.loads((source / 'results.json').read_text())
    expected_scaling = json.loads((source / 'scaling.json').read_text())
    if len(expected['ladder']) != 10 or len(expected_scaling) != 4:
        raise AssertionError('Unexpected published fixture counts')
    with tempfile.TemporaryDirectory(prefix='ct-public-memory-') as temporary:
        work = Path(temporary)
        for name in ('benchmark.py', 'run_single.py', 'destructive_check.py'):
            shutil.copyfile(source / name, work / name)
        if full:
            command([sys.executable, 'benchmark.py'], work)
            fresh = json.loads((work / 'results.json').read_text())
            rows, baseline = fresh['ladder'], expected['ladder']
            if len(rows) != 10 or len(fresh['scaling']) != 4:
                raise AssertionError('Unexpected ladder/scaling counts')
            for row, old in zip(fresh['scaling'], expected_scaling):
                for key in ('n_words', 'raw_bytes', 'causal_bytes'):
                    if row[key] != old[key]:
                        raise AssertionError('Scaling mismatch: ' + key)
        else:
            command([sys.executable, 'run_single.py', '1.0', '--index', '9'], work)
            rows = [json.loads((work / 'level_09_1.000000.json').read_text())]
            baseline = [expected['ladder'][9]]
        for row, old in zip(rows, baseline):
            for key in ('raw_sha256', 'raw_bytes', 'causal_bytes', 'causal_mode',
                        'blind_discovery', 'blind_discovery_hits', 'causal_replay_exact'):
                if row[key] != old[key]:
                    raise AssertionError('Memory benchmark mismatch: ' + key)
            if row['causal_replay_exact'] is not True:
                raise AssertionError('Exact replay failed')
        command([sys.executable, 'destructive_check.py'], work)
        destructive = json.loads((work / 'destructive_check.json').read_text())
        if len(destructive) != 3 or not all(all(r[k] for k in
                ('source_deleted_before_decode', 'byte_identical', 'sha256_match', 'corruption_blocked'))
                for r in destructive):
            raise AssertionError('Destructive-source checks failed')
    return {
        'status': 'PASS_SCOPED', 'mode': 'full_public_ladder' if full else 'published_100_percent_point',
        'ladder_rows_executed': len(rows), 'scaling_rows_executed': 4 if full else 0,
        'raw_hashes_and_causal_sizes_match_published': True,
        'causal_bytes': [r['causal_bytes'] for r in rows],
        'conventional_codecs_per_row': 7, 'destructive_checks_passed': 3,
        'versions': versions,
        'not_run': ['PASS016 60 core tests', 'PASS016 105 proof checks',
                    'PASS016 17 adversarial tests', 'original 11JSON corpus benchmark'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['all', 'memory', 'alignment'], default='all')
    parser.add_argument('--full-memory', action='store_true', help='Run all 10 published rows and 4 scaling rows')
    parser.add_argument('--output', type=Path, help='Write fresh JSON receipt to a new file; never overwrite')
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Run without -O/PYTHONOPTIMIZE; upstream checks use assertions')
    if args.output and args.output.exists():
        parser.error('Output already exists; choose a new receipt path')
    started = time.monotonic()
    report = {'schema': 1, 'python': platform.python_version(), 'platform': platform.platform(),
              'verified_source_files': verify_sources(), 'scope': 'public executable subset only'}
    if args.suite in ('all', 'alignment'):
        report['alignment'] = alignment()
    if args.suite in ('all', 'memory'):
        report['memory'] = memory(args.full_memory)
    report['elapsed_seconds'] = time.monotonic() - started
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(text)
    print(text, end='')


if __name__ == '__main__':
    main()
