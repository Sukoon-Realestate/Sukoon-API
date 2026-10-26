"""Verify final-batch source coverage and exported artifacts without changing app files."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORKSPACE = BASE.parents[3]

def read(path):
    return json.loads(path.read_text())

def verify_hash(record):
    path = WORKSPACE / record['source']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path

def dimensions(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    return struct.unpack('>II', data[16:24])

audit = read(HERE / 'batch-11-14-source-audit.json')
assert len(audit) == 75
by_source = {x['source']: x for x in audit}
manifest = []
exports = []
subpages = []
per_sprint = []
for n in range(11, 15):
    folder = HERE / f'sprint-{n:02}'
    screens = read(folder / 'screen-manifest.json')
    assert len(screens) == (15 if n == 14 else 20)
    report = read(folder / 'review-results.json')
    assert report['result'] == 'pass' and not report['errors'] and not report['externalRequests']
    for screen in screens:
        verify_hash(screen)
        for dependency in screen['dependencies']:
            verify_hash(dependency)
        native = by_source[screen['source']]['classes']
        assert set(native) == set(screen['coveredNativeClasses']), screen['id']
        assert set(screen['requiredStates']) <= set(screen['renderedVariants']) | {'invalid', 'dirty'}, screen['id']
        for native_class, state in screen['coveredNativeClasses'].items():
            assert state == 'default' or state in screen['renderedVariants']
            if state != 'default':
                for theme in ['light', 'dark']:
                    p = folder / 'exports/native-subpages' / f'{native_class}-{theme}.png'
                    assert dimensions(p) == (720, 1600), p
                    subpages.append(str(p.relative_to(HERE)))
        for theme in ['light', 'dark']:
            p = folder / 'exports' / f"{screen['id']}-{theme}.png"
            assert dimensions(p) == (720, 1600), p
            exports.append(str(p.relative_to(HERE)))
    pngs = list((folder / 'exports').rglob('*.png'))
    sheets = list((folder / 'exports').glob('*-sheet-*.png'))
    overviews = list((folder / 'exports').glob('*-overview.png'))
    assert len(sheets) == (8 if n == 14 else 10) and len(overviews) == 2
    per_sprint.append(dict(sprint=n, primaryScreens=len(screens), pngs=len(pngs), sheets=len(sheets), overviews=len(overviews)))
    manifest.extend(screens)
assert {x['id'] for x in manifest} == {f'S{x}' for x in range(221, 296)}
assert len(exports) == 150 and len(subpages) == 26
assert sum(x['pngs'] for x in per_sprint) == 222

original = read(BASE / 'screen-manifest.json')
all_screens = original[:]
for n in range(1, 15):
    all_screens.extend(read(HERE / f'sprint-{n:02}/screen-manifest.json'))
ids = [x['id'] for x in all_screens]
inventory = read(HERE / 'screen-inventory.json')
assert len(ids) == len(set(ids)) == 295
assert set(ids) == {x['proposalId'] for x in inventory['screens'] if x.get('proposalId')}
assert inventory['proposalCoverage']['status'] == 'complete'
assert not inventory['proposalCoverage']['unbuiltDestinations']
native_status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=WORKSPACE / 'sokoun', text=True)
assert not native_status.strip(), native_status
dependencies = {d['source'] for x in audit for d in x['dependencies']}
result = dict(result='pass', primaryScreens=75, nativeClasses=sum(len(x['classes']) for x in audit),
              dependencyReferences=sum(len(x['dependencies']) for x in audit), uniqueDependencies=len(dependencies),
              sourceHashes='all match', nativeSubpageVariants=13, primaryExports=len(exports),
              nativeSubpageExports=len(subpages), pngs=222, individualDimensions=[720, 1600],
              sprints=per_sprint, galleryPrimaryScreens=295, gallerySections=15,
              unbuiltDestinations=0, nativeChanges=False)
(HERE / 'batch-11-14-source-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
