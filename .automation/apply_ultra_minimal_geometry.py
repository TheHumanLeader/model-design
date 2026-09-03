from pathlib import Path

root = Path(__file__).resolve().parents[1]

core_path = root / 'src/core/document.ts'
core = core_path.read_text(encoding='utf-8')
old_constant = 'export const MODEL_NODE_BASE_HEIGHT = 110'
new_constant = 'export const MODEL_NODE_BASE_HEIGHT = 88'
if core.count(old_constant) != 1:
    raise RuntimeError(
        f'Expected one node-height constant, found {core.count(old_constant)}'
    )
core_path.write_text(core.replace(old_constant, new_constant, 1), encoding='utf-8')

test_path = root / 'tests/document.test.ts'
tests = test_path.read_text(encoding='utf-8')
replacements = {
    'expect(modelHeight(model)).toBe(110)': 'expect(modelHeight(model)).toBe(88)',
    'expect(compactHeight).toBe(110)': 'expect(compactHeight).toBe(88)',
}
for old, new in replacements.items():
    if tests.count(old) != 1:
        raise RuntimeError(f'Expected one test assertion `{old}`, found {tests.count(old)}')
    tests = tests.replace(old, new, 1)
test_path.write_text(tests, encoding='utf-8')

print('Ultra-minimal node geometry applied')
