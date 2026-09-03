from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


# 1. Central relationship cardinality semantics.
types_path = ROOT / "src/types.ts"
types = types_path.read_text(encoding="utf-8")
types = replace_once(
    types,
    """export const MODEL_RELATION_TYPE_LABELS: Record<ModelRelationType, string> = {
  'one-to-one': '一对一',
  'one-to-many': '一对多',
  'many-to-one': '多对一',
  'many-to-many': '多对多',
}
""",
    """export const MODEL_RELATION_TYPE_LABELS: Record<ModelRelationType, string> = {
  'one-to-one': '一对一',
  'one-to-many': '一对多',
  'many-to-one': '多对一',
  'many-to-many': '多对多',
}

export type ModelRelationCardinality = '1' | 'N'

/**
 * Relationship cardinality is always read from the field owner (source)
 * toward the selected target model.
 */
export const MODEL_RELATION_CARDINALITIES: Record<
  ModelRelationType,
  readonly [ModelRelationCardinality, ModelRelationCardinality]
> = {
  'one-to-one': ['1', '1'],
  'one-to-many': ['1', 'N'],
  'many-to-one': ['N', '1'],
  'many-to-many': ['N', 'N'],
}
""",
    "relation cardinality map",
)
types_path.write_text(types, encoding="utf-8")


# 2. Fix all field-panel native selects for Vapor and clarify source -> target.
fields_path = ROOT / "src/components/ModelFieldsPanel.vue"
fields = fields_path.read_text(encoding="utf-8")
fields = replace_once(
    fields,
    """import { MODEL_FIELD_TYPES, MODEL_RELATION_TYPES } from '../types'
""",
    """import {
  MODEL_FIELD_TYPES,
  MODEL_RELATION_CARDINALITIES,
  MODEL_RELATION_TYPES,
} from '../types'
""",
    "field panel imports",
)
fields = replace_once(
    fields,
    """const relationTypeLabels: Record<ModelRelationType, string> = {
  'one-to-one': '1 : 1',
  'one-to-many': '1 : N',
  'many-to-one': 'N : 1',
  'many-to-many': 'N : N',
}
""",
    """const relationTypeLabels: Record<ModelRelationType, string> = {
  'one-to-one': '当前 1 → 目标 1',
  'one-to-many': '当前 1 → 目标 N',
  'many-to-one': '当前 N → 目标 1',
  'many-to-many': '当前 N → 目标 N',
}
""",
    "unambiguous field relation labels",
)
fields = replace_once(
    fields,
    """                  :value="fieldType"
                >
""",
    """                  :value="fieldType"
                  :selected="field.type === fieldType"
                >
""",
    "field type selected binding",
)
fields = replace_once(
    fields,
    """              <small>当前字段 → 目标模型字段</small>
""",
    """              <small>基数按“当前模型 → 目标模型”读取</small>
""",
    "relationship direction hint",
)
fields = replace_once(
    fields,
    """                  <option value="">无关系</option>
""",
    """                  <option value="" :selected="!field.relation?.modelId">无关系</option>
""",
    "empty relation model selected binding",
)
fields = replace_once(
    fields,
    """                    :value="candidate.id"
                  >
""",
    """                    :value="candidate.id"
                    :selected="field.relation?.modelId === candidate.id"
                  >
""",
    "relation target model selected binding",
)
fields = replace_once(
    fields,
    """                    <option value="">仅关联模型</option>
""",
    """                    <option value="" :selected="!field.relation.fieldId">仅关联模型</option>
""",
    "empty target field selected binding",
)
fields = replace_once(
    fields,
    """                      :value="targetField.id"
                    >
""",
    """                      :value="targetField.id"
                      :selected="field.relation.fieldId === targetField.id"
                    >
""",
    "relation target field selected binding",
)
fields = replace_once(
    fields,
    """                      :value="relationType"
                    >
""",
    """                      :value="relationType"
                      :selected="field.relation.type === relationType"
                    >
""",
    "relation type selected binding",
)
fields = replace_once(
    fields,
    """                </label>

                <label class="md-compact-field is-wide">
                  <span>关系名称</span>
""",
    """                </label>

                <div class="md-relation-direction is-wide">
                  <small>当前模型 → 目标模型</small>
                  <strong>
                    <b>{{ MODEL_RELATION_CARDINALITIES[field.relation.type][0] }}</b>
                    <span>{{ model.name || '当前模型' }}</span>
                    <i aria-hidden="true">→</i>
                    <b>{{ MODEL_RELATION_CARDINALITIES[field.relation.type][1] }}</b>
                    <span>{{ relationTarget(field)?.name || '目标模型' }}</span>
                  </strong>
                </div>

                <label class="md-compact-field is-wide">
                  <span>关系名称</span>
""",
    "relation live preview",
)
fields_path.write_text(fields, encoding="utf-8")


# 3. Fix group select in the inspector.
inspector_path = ROOT / "src/components/ModelInspector.vue"
inspector = inspector_path.read_text(encoding="utf-8")
inspector = replace_once(
    inspector,
    """                <option value="">根画板</option>
""",
    """                <option value="" :selected="!model.groupId">根画板</option>
""",
    "empty group selected binding",
)
inspector = replace_once(
    inspector,
    """                  :value="candidate.id"
                >
""",
    """                  :value="candidate.id"
                  :selected="model.groupId === candidate.id"
                >
""",
    "group selected binding",
)
inspector_path.write_text(inspector, encoding="utf-8")


# 4. Fix all trigger native selects for Vapor.
triggers_path = ROOT / "src/components/ModelTriggersPanel.vue"
triggers = triggers_path.read_text(encoding="utf-8")
triggers = replace_once(
    triggers,
    """                  :value="source"
                >
""",
    """                  :value="source"
                  :selected="item.source === source"
                >
""",
    "trigger source selected binding",
)
triggers = replace_once(
    triggers,
    """                  :value="timing"
                >
""",
    """                  :value="timing"
                  :selected="item.timing === timing"
                >
""",
    "trigger timing selected binding",
)
triggers = replace_once(
    triggers,
    """                <option value="">任意字段</option>
""",
    """                <option value="" :selected="!item.fieldId">任意字段</option>
""",
    "empty trigger field selected binding",
)
triggers = replace_once(
    triggers,
    """                  :value="field.id"
                >
""",
    """                  :value="field.id"
                  :selected="item.fieldId === field.id"
                >
""",
    "trigger field selected binding",
)
triggers = replace_once(
    triggers,
    """                <option value="">未绑定</option>
""",
    """                <option value="" :selected="!item.eventId">未绑定</option>
""",
    "empty trigger event selected binding",
)
triggers = replace_once(
    triggers,
    """                  :value="eventItem.id"
                >
""",
    """                  :value="eventItem.id"
                  :selected="item.eventId === eventItem.id"
                >
""",
    "trigger event selected binding",
)
triggers_path.write_text(triggers, encoding="utf-8")


# 5. Put exact 1/N cardinality into every relation line.
designer_path = ROOT / "src/components/ModelDesigner.vue"
designer = designer_path.read_text(encoding="utf-8")
designer = replace_once(
    designer,
    """import { MODEL_RELATION_TYPE_LABELS } from '../types'
""",
    """import {
  MODEL_RELATION_CARDINALITIES,
  MODEL_RELATION_TYPE_LABELS,
} from '../types'
""",
    "designer relation imports",
)
designer = replace_once(
    designer,
    """  endX: number
  endY: number
}
""",
    """  endX: number
  endY: number
  sourceCardinality: '1' | 'N'
  targetCardinality: '1' | 'N'
}
""",
    "designer relation line cardinalities",
)
designer = replace_once(
    designer,
    """  const relationType = MODEL_RELATION_TYPE_LABELS[edge.relation.type] ?? '关联'
  const label = `${relationName} · ${relationType}`
""",
    """  const relationType = MODEL_RELATION_TYPE_LABELS[edge.relation.type] ?? '关联'
  const [sourceCardinality, targetCardinality] =
    MODEL_RELATION_CARDINALITIES[edge.relation.type]
  const label = `${relationName} · ${sourceCardinality} → ${targetCardinality}`
""",
    "relation cardinality label",
)
designer = replace_once(
    designer,
    """      endX: startX,
      endY,
    }
""",
    """      endX: startX,
      endY,
      sourceCardinality,
      targetCardinality,
    }
""",
    "self relation cardinalities",
)
designer = replace_once(
    designer,
    """    endX,
    endY,
  }
}
""",
    """    endX,
    endY,
    sourceCardinality,
    targetCardinality,
  }
}
""",
    "normal relation cardinalities",
)
designer_path.write_text(designer, encoding="utf-8")


# 6. Render endpoint cardinality badges in the relation layer.
relations_path = ROOT / "src/components/ModelRelations.vue"
relations = relations_path.read_text(encoding="utf-8")
relations = replace_once(
    relations,
    """  endX: number
  endY: number
}
""",
    """  endX: number
  endY: number
  sourceCardinality: '1' | 'N'
  targetCardinality: '1' | 'N'
}
""",
    "relation component cardinalities",
)
relations = replace_once(
    relations,
    """      <circle
        class="md-relation-line__terminal is-target"
        :cx="line.endX"
        :cy="line.endY"
        r="6"
      ></circle>

      <path class="md-relation-line__halo" :d="line.path"></path>
""",
    """      <circle
        class="md-relation-line__terminal is-target"
        :cx="line.endX"
        :cy="line.endY"
        r="6"
      ></circle>

      <g
        class="md-relation-cardinality is-source"
        :transform="`translate(${line.startX + (line.endX >= line.startX ? 16 : -16)} ${line.startY - 13})`"
      >
        <rect x="-10" y="-8" width="20" height="16" rx="8"></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.sourceCardinality }}</text>
      </g>
      <g
        class="md-relation-cardinality is-target"
        :transform="`translate(${line.endX + (line.endX >= line.startX ? -16 : 16)} ${line.endY - 13})`"
      >
        <rect x="-10" y="-8" width="20" height="16" rx="8"></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.targetCardinality }}</text>
      </g>

      <path class="md-relation-line__halo" :d="line.path"></path>
""",
    "relation endpoint badges",
)
relations_path.write_text(relations, encoding="utf-8")


# 7. Dense relationship preview and endpoint badge styling.
style_path = ROOT / "src/styles/relation-cardinality.css"
style_path.write_text(
    """.md-relation-direction {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid color-mix(in srgb, var(--md-accent) 18%, var(--md-line));
  border-radius: 9px;
  background: color-mix(in srgb, var(--md-accent-soft) 24%, transparent);
}

.md-relation-direction > small {
  color: var(--md-faint);
  font-size: 8px;
}

.md-relation-direction > strong {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
  color: var(--md-text);
  font-size: 9px;
  font-weight: 650;
}

.md-relation-direction > strong span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.md-relation-direction > strong b {
  display: inline-grid;
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 7px;
  color: var(--md-accent);
  background: var(--md-panel-solid);
  font-size: 9px;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--md-accent) 18%, var(--md-line));
}

.md-relation-direction > strong i {
  flex: 0 0 auto;
  color: var(--md-accent);
  font-style: normal;
}

.md-relation-cardinality {
  opacity: 0;
  pointer-events: none;
  animation: md-relation-cardinality-enter 0.35s calc(var(--md-edge-delay) + 0.9s) ease-out forwards;
}

.md-relation-cardinality rect {
  fill: color-mix(in srgb, var(--md-panel-solid) 94%, transparent);
  stroke: color-mix(in srgb, var(--md-accent) 42%, var(--md-line));
  stroke-width: 1px;
  vector-effect: non-scaling-stroke;
}

.md-relation-cardinality.is-target rect {
  stroke: color-mix(in srgb, var(--md-success) 58%, var(--md-line));
}

.md-relation-cardinality text {
  fill: var(--md-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 8px;
  font-weight: 850;
}

@keyframes md-relation-cardinality-enter {
  from {
    opacity: 0;
    scale: 0.7;
  }

  to {
    opacity: 1;
    scale: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .md-relation-cardinality {
    animation-duration: 0.001ms !important;
    animation-delay: 0ms !important;
  }
}
""",
    encoding="utf-8",
)

index_path = ROOT / "src/styles/index.css"
index = index_path.read_text(encoding="utf-8")
if "@import './relation-cardinality.css';" not in index:
    index = index.rstrip() + "\n@import './relation-cardinality.css';\n"
index_path.write_text(index, encoding="utf-8")


# 8. Lock cardinality semantics with unit tests.
test_path = ROOT / "tests/relation-cardinality.test.ts"
test_path.write_text(
    """import { describe, expect, it } from 'vitest'
import {
  MODEL_RELATION_CARDINALITIES,
  MODEL_RELATION_TYPE_LABELS,
} from '../src/types'

describe('relationship cardinality semantics', () => {
  it.each([
    ['one-to-one', ['1', '1'], '一对一'],
    ['one-to-many', ['1', 'N'], '一对多'],
    ['many-to-one', ['N', '1'], '多对一'],
    ['many-to-many', ['N', 'N'], '多对多'],
  ] as const)('maps %s from source to target', (type, expected, label) => {
    expect(MODEL_RELATION_CARDINALITIES[type]).toEqual(expected)
    expect(MODEL_RELATION_TYPE_LABELS[type]).toBe(label)
  })
})
""",
    encoding="utf-8",
)

print('Vapor select synchronization and relation cardinality fix applied')
