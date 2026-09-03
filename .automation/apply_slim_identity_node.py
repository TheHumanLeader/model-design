from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Keep geometry, collision, grouping and fit-view calculations aligned with the visual node.
core_path = ROOT / "src/core/document.ts"
replace_exact(
    core_path,
    "export const MODEL_NODE_BASE_HEIGHT = 88",
    "export const MODEL_NODE_BASE_HEIGHT = 56",
    "model node base height",
)

# Update the two geometry regression expectations.
test_path = ROOT / "tests/document.test.ts"
tests = test_path.read_text(encoding="utf-8")
expected = tests.count("toBe(88)")
if expected != 2:
    raise RuntimeError(f"node height expectations: expected 2 matches, found {expected}")
test_path.write_text(tests.replace("toBe(88)", "toBe(56)"), encoding="utf-8")

# Final override: a real compact identity row, not a padded card.
style_path = ROOT / "src/styles/slim-identity-node.css"
style_path.write_text(
    r'''/* Final compact canvas node: icon + title + subtitle only. */
.md-model-node:not(.is-relation-card) {
  height: var(--md-node-height, 56px);
  border-color: color-mix(in srgb, var(--md-line) 72%, transparent);
  border-radius: 8px;
  box-shadow: none;
}

.md-model-node:not(.is-relation-card):hover {
  border-color: color-mix(in srgb, var(--md-text) 18%, var(--md-line));
  box-shadow: 0 3px 10px color-mix(in srgb, #18213a 6%, transparent);
}

.md-model-node:not(.is-relation-card).is-selected {
  border-color: color-mix(in srgb, var(--md-accent) 62%, var(--md-line));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--md-accent) 10%, transparent);
}

.md-model-node:not(.is-relation-card) .md-model-node__header {
  height: 100%;
  gap: 9px;
  padding: 0 9px;
}

.md-model-node:not(.is-relation-card) .md-model-node__icon {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: color-mix(in srgb, var(--md-accent-soft) 62%, transparent);
}

.md-model-node:not(.is-relation-card) .md-model-node__icon svg {
  width: 12px;
  height: 12px;
  stroke-width: 1.65;
}

.md-model-node:not(.is-relation-card) .md-model-node__identity {
  gap: 1px;
}

.md-model-node:not(.is-relation-card) .md-model-node__title {
  font-size: 12px;
  font-weight: 710;
  line-height: 1.18;
}

.md-model-node:not(.is-relation-card) .md-model-node__code {
  font-size: 7px;
  line-height: 1.1;
  letter-spacing: 0.03em;
}

.md-model-node:not(.is-relation-card) .md-model-node__menu {
  width: 19px;
  height: 19px;
  border-radius: 6px;
}

.md-model-node:not(.is-relation-card) .md-model-node__menu span {
  width: 2.5px;
  height: 2.5px;
}
''',
    encoding="utf-8",
)

index_path = ROOT / "src/styles/index.css"
index_source = index_path.read_text(encoding="utf-8")
import_line = "@import './slim-identity-node.css';"
if import_line not in index_source:
    index_source = index_source.rstrip() + f"\n{import_line}\n"
index_path.write_text(index_source, encoding="utf-8")

print("Slim identity node applied")
