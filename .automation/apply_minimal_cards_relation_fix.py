from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(
    text: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError(f"{label}: section markers not found")
    return text[:start] + replacement + text[end:]


# Keep canvas geometry aligned with the new compact cards.
core_path = ROOT / "src/core/document.ts"
core = core_path.read_text(encoding="utf-8")
core = replace_once(
    core,
    "export const MODEL_NODE_BASE_HEIGHT = 167",
    "export const MODEL_NODE_BASE_HEIGHT = 110",
    "base model height constant",
)
core = replace_once(
    core,
    """export function modelHeight(model: ModelNode): number {
  const tagHeight = (model.tags?.length ?? 0) > 0 ? 34 : 0
  return 58 + 43 + tagHeight + 25
}

export function relationModelHeight(
  model: ModelNode,
  relationFieldCount: number,
): number {
  const normalizedCount = Math.max(0, relationFieldCount)
  const visibleFieldCount = Math.min(normalizedCount, 6)
  const fieldAreaHeight =
    visibleFieldCount === 0
      ? 48
      : 14 +
        visibleFieldCount * 31 +
        (normalizedCount > 6 ? 34 : 0)

  return modelHeight(model) + 28 + fieldAreaHeight
}
""",
    """export function modelHeight(_model: ModelNode): number {
  return MODEL_NODE_BASE_HEIGHT
}

export function relationModelHeight(
  _model: ModelNode,
  relationFieldCount: number,
): number {
  const normalizedCount = Math.max(0, relationFieldCount)
  const visibleFieldCount = Math.min(normalizedCount, 6)
  const fieldBodyHeight =
    visibleFieldCount === 0 ? 46 : visibleFieldCount * 38
  const overflowHeight = normalizedCount > 6 ? 28 : 0

  return 50 + 16 + fieldBodyHeight + overflowHeight
}
""",
    "compact model geometry",
)
core_path.write_text(core, encoding="utf-8")


# Replace the node presentation with a smaller, quieter card.
node_path = ROOT / "src/components/ModelNode.vue"
node_path.write_text(
    '''<script setup lang="ts" vapor>
import { computed } from 'vue'
import { modelHeight, relationModelHeight } from '../core'
import type { ModelField, ModelNode } from '../types'

const props = withDefaults(
  defineProps<{
    model: ModelNode
    x: number
    y: number
    selected: boolean
    dragging: boolean
    relationState: 'none' | 'focus' | 'related' | 'dimmed'
    relationCount: number
    detail?: boolean
    detailFieldIds?: string[]
    appearanceIndex?: number
    interactive?: boolean
  }>(),
  {
    detail: false,
    detailFieldIds: () => [],
    appearanceIndex: 0,
    interactive: true,
  },
)

const emit = defineEmits<{
  pointerdown: [modelId: string, event: PointerEvent]
  contextmenu: [modelId: string, event: MouseEvent]
  menu: [modelId: string, event: MouseEvent]
  doubleclick: [modelId: string]
}>()

const detailFields = computed<ModelField[]>(() => {
  if (!props.detail) return []

  const ids = new Set(props.detailFieldIds)
  return props.model.fields.filter((field) => ids.has(field.id))
})

const visibleFields = computed(() => detailFields.value.slice(0, 6))
const hiddenFieldCount = computed(() =>
  Math.max(0, detailFields.value.length - visibleFields.value.length),
)
const visibleTags = computed(() => (props.model.tags ?? []).slice(0, 2))
const hiddenTagCount = computed(() =>
  Math.max(0, (props.model.tags ?? []).length - visibleTags.value.length),
)
const nodeHeight = computed(() =>
  props.detail
    ? relationModelHeight(props.model, detailFields.value.length)
    : modelHeight(props.model),
)

const nodeStyle = computed(() => ({
  '--md-node-x': `${props.x}px`,
  '--md-node-y': `${props.y}px`,
  '--md-node-width': `${props.model.width}px`,
  '--md-node-height': `${nodeHeight.value}px`,
  '--md-relation-delay': `${Math.min(props.appearanceIndex, 12) * 72}ms`,
}))

function handlePointerDown(event: PointerEvent): void {
  if (!props.interactive) return
  emit('pointerdown', props.model.id, event)
}

function handleContextMenu(event: MouseEvent): void {
  if (!props.interactive) return
  emit('contextmenu', props.model.id, event)
}

function handleMenu(event: MouseEvent): void {
  if (!props.interactive) return
  emit('menu', props.model.id, event)
}

function handleDoubleClick(): void {
  if (!props.interactive) return
  emit('doubleclick', props.model.id)
}
</script>

<template>
  <article
    class="md-model-node"
    :class="{
      'is-selected': selected,
      'is-dragging': dragging,
      'is-relation-card': detail,
      'is-relation-focus': relationState === 'focus',
      'is-relation-related': relationState === 'related',
      'is-relation-dimmed': relationState === 'dimmed',
      'is-static': !interactive,
    }"
    :style="nodeStyle"
    :data-model-id="model.id"
    :data-relation-field-count="detail ? detailFields.length : undefined"
    @pointerdown.stop="handlePointerDown"
    @contextmenu.prevent.stop="handleContextMenu"
    @dblclick.stop="handleDoubleClick"
  >
    <header class="md-model-node__header">
      <span class="md-model-node__mark" aria-hidden="true"></span>

      <span class="md-model-node__title-wrap">
        <strong class="md-model-node__title">{{ model.name || '未命名模型' }}</strong>
        <span class="md-model-node__code">{{ model.code || 'unnamed_model' }}</span>
      </span>

      <span v-if="detail" class="md-model-node__role">
        <i></i>
        {{ relationState === 'focus' ? '焦点' : '关联' }}
        <b>{{ detailFields.length }}</b>
      </span>

      <button
        v-else-if="interactive"
        class="md-model-node__menu"
        type="button"
        title="模型菜单"
        aria-label="打开模型菜单"
        @pointerdown.stop
        @click.stop="handleMenu"
        @contextmenu.prevent.stop="handleMenu"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
    </header>

    <template v-if="!detail">
      <p class="md-model-node__purpose">
        {{ model.purpose || '未填写模型用途' }}
      </p>

      <div class="md-model-node__meta">
        <span class="md-model-node__tag-list">
          <template v-if="visibleTags.length">
            <span v-for="tag in visibleTags" :key="tag" class="md-model-node__tag">
              {{ tag }}
            </span>
            <span v-if="hiddenTagCount" class="md-model-node__tag is-more">
              +{{ hiddenTagCount }}
            </span>
          </template>
          <span v-else class="md-model-node__tag-empty">无标签</span>
        </span>

        <span class="md-model-node__metrics">
          <b title="字段">F {{ model.fields.length }}</b>
          <b title="事件 / Function">Fn {{ model.events.length }}</b>
          <b title="触发器">T {{ model.triggers.length }}</b>
          <b v-if="relationCount" title="关系">R {{ relationCount }}</b>
        </span>
      </div>
    </template>

    <div v-else class="md-model-node__fields">
      <template v-if="visibleFields.length">
        <div
          v-for="field in visibleFields"
          :key="field.id"
          class="md-model-node__field"
          :data-field-id="field.id"
        >
          <span class="md-model-node__field-name">
            <span v-if="field.primaryKey" class="md-model-node__key" title="主键">◆</span>
            <span v-if="field.relation" class="md-model-node__relation-icon" title="关系字段">↗</span>
            <span class="md-model-node__field-copy">
              <strong>{{ field.name || '未命名字段' }}</strong>
              <small>{{ field.code || 'unnamed_field' }}</small>
            </span>
            <span v-if="field.required" class="md-model-node__required">*</span>
          </span>
          <code>{{ field.type }}</code>
        </div>

        <div v-if="hiddenFieldCount" class="md-model-node__field-more">
          还有 {{ hiddenFieldCount }} 个相关字段
        </div>
      </template>

      <div v-else class="md-model-node__empty">
        关联模型整体
      </div>
    </div>
  </article>
</template>
''',
    encoding="utf-8",
)


# Relation mode uses an independent, evenly spaced star layout and field anchors.
designer_path = ROOT / "src/components/ModelDesigner.vue"
designer = designer_path.read_text(encoding="utf-8")

designer = replace_once(
    designer,
    """const relationFieldIdsByModelId = computed(() => {
  const fieldsByModel = new Map<string, Set<string>>()

  const addField = (modelId: string, fieldId: string | null | undefined) => {
    if (!fieldId) return
    const fieldIds = fieldsByModel.get(modelId) ?? new Set<string>()
    fieldIds.add(fieldId)
    fieldsByModel.set(modelId, fieldIds)
  }

  focusedRelationEdges.value.forEach((edge) => {
    addField(edge.sourceModelId, edge.sourceField.id)
    addField(edge.targetModelId, edge.targetField?.id)
  })

  return fieldsByModel
})
const relationLines = computed<RelationLine[]>(() =>
""",
    """const relationFieldIdsByModelId = computed(() => {
  const fieldsByModel = new Map<string, Set<string>>()

  const addField = (modelId: string, fieldId: string | null | undefined) => {
    if (!fieldId) return
    const fieldIds = fieldsByModel.get(modelId) ?? new Set<string>()
    fieldIds.add(fieldId)
    fieldsByModel.set(modelId, fieldIds)
  }

  focusedRelationEdges.value.forEach((edge) => {
    addField(edge.sourceModelId, edge.sourceField.id)
    addField(edge.targetModelId, edge.targetField?.id)
  })

  return fieldsByModel
})
const relationLayoutPositions = computed(() => {
  const positions = new Map<string, Point>()
  const focus = relationFocusModel.value
  if (!focus) return positions

  positions.set(focus.id, {
    x: 0,
    y: -relationNodeHeight(focus) / 2,
  })

  const related = relationVisibleModels.value.filter((model) => model.id !== focus.id)
  const columnCapacity = 4
  const columnCount = Math.max(1, Math.ceil(related.length / columnCapacity))

  for (let column = 0; column < columnCount; column += 1) {
    const items = related.slice(
      column * columnCapacity,
      (column + 1) * columnCapacity,
    )
    const verticalGap = 46
    const totalHeight =
      items.reduce((sum, model) => sum + relationNodeHeight(model), 0) +
      Math.max(0, items.length - 1) * verticalGap
    let cursorY = -totalHeight / 2

    items.forEach((model) => {
      positions.set(model.id, {
        x: 500 + column * 400,
        y: cursorY,
      })
      cursorY += relationNodeHeight(model) + verticalGap
    })
  }

  return positions
})
const relationLines = computed<RelationLine[]>(() =>
""",
    "relation layout positions",
)

designer = replace_between(
    designer,
    "function relationFieldIds(modelId: string): string[] {",
    "function groupRelationState(",
    """function relationFieldIds(modelId: string): string[] {
  return [...(relationFieldIdsByModelId.value.get(modelId) ?? [])]
}

function relationFieldsForModel(model: ModelNode): ModelField[] {
  const ids = new Set(relationFieldIds(model.id))
  return model.fields.filter((field) => ids.has(field.id))
}

function relationNodeIndex(modelId: string): number {
  return Math.max(
    0,
    relationVisibleModels.value.findIndex((model) => model.id === modelId),
  )
}

function relationNodeHeight(model: ModelNode): number {
  return relationModelHeight(model, relationFieldIds(model.id).length)
}

function relationModelPosition(modelId: string): Point {
  return (
    relationLayoutPositions.value.get(modelId) ??
    designDocument.value.models.find((model) => model.id === modelId) ??
    { x: 0, y: 0 }
  )
}

function relationModelX(model: ModelNode): number {
  return relationModelPosition(model.id).x
}

function relationModelY(model: ModelNode): number {
  return relationModelPosition(model.id).y
}

function relationFieldAnchorY(
  model: ModelNode,
  fieldId: string | null | undefined,
): number {
  const fields = relationFieldsForModel(model)
  const rawIndex = fieldId
    ? fields.findIndex((field) => field.id === fieldId)
    : -1
  const rowIndex = Math.min(Math.max(rawIndex, 0), 5)
  const rowCenter = fields.length > 0 ? rowIndex * 38 + 19 : 23

  return relationModelY(model) + 50 + 8 + rowCenter
}

""",
    "relation model helpers",
)

designer = replace_between(
    designer,
    "function createRelationLine(edge: RelationEdge): RelationLine | null {",
    "function cubicPoint(",
    """function createRelationLine(edge: RelationEdge): RelationLine | null {
  const source = designDocument.value.models.find(
    (model) => model.id === edge.sourceModelId,
  )
  const target = designDocument.value.models.find(
    (model) => model.id === edge.targetModelId,
  )
  if (!source || !target) return null

  const sourceRect = {
    x: relationModelX(source),
    y: relationModelY(source),
    width: source.width,
    height: relationNodeHeight(source),
  }
  const targetRect = {
    x: relationModelX(target),
    y: relationModelY(target),
    width: target.width,
    height: relationNodeHeight(target),
  }
  const sourceAnchorY = relationFieldAnchorY(source, edge.sourceField.id)
  const targetAnchorY = relationFieldAnchorY(target, edge.targetField?.id)

  const sourceName = edge.sourceField.name || edge.sourceField.code || '关系字段'
  const relationName = (edge.relation.label ?? '').trim() || sourceName
  const relationType = MODEL_RELATION_TYPE_LABELS[edge.relation.type] ?? '关联'
  const label = `${relationName} · ${relationType}`
  const labelWidth = Math.min(180, Math.max(76, [...label].length * 7.2 + 20))

  if (source.id === target.id) {
    const startX = sourceRect.x + sourceRect.width
    const startY = sourceAnchorY
    const endY = Math.max(startY + 38, targetAnchorY)
    const loopX = startX + 116

    return {
      id: edge.id,
      path: `M ${startX} ${startY} C ${loopX} ${startY - 44}, ${loopX} ${endY + 44}, ${startX} ${endY}`,
      label,
      labelX: loopX - 4,
      labelY: (startY + endY) / 2 - 18,
      labelWidth,
      startX,
      startY,
      endX: startX,
      endY,
    }
  }

  const sourceCenterX = sourceRect.x + sourceRect.width / 2
  const targetCenterX = targetRect.x + targetRect.width / 2
  const direction = targetCenterX >= sourceCenterX ? 1 : -1
  const startX = direction > 0 ? sourceRect.x + sourceRect.width : sourceRect.x
  const endX = direction > 0 ? targetRect.x : targetRect.x + targetRect.width
  const startY = sourceAnchorY
  const endY = targetAnchorY
  const distance = Math.abs(endX - startX)
  const curve = Math.min(260, Math.max(90, distance * 0.48))
  const control1X = startX + direction * curve
  const control1Y = startY
  const control2X = endX - direction * curve
  const control2Y = endY
  const labelX = cubicPoint(startX, control1X, control2X, endX, 0.5)
  const labelY = cubicPoint(startY, control1Y, control2Y, endY, 0.5) - 18

  return {
    id: edge.id,
    path: `M ${startX} ${startY} C ${control1X} ${control1Y}, ${control2X} ${control2Y}, ${endX} ${endY}`,
    label,
    labelX,
    labelY,
    labelWidth,
    startX,
    startY,
    endX,
    endY,
  }
}

""",
    "field anchored relation lines",
)

designer = replace_between(
    designer,
    "function fitRelationView(): void {",
    "function screenToWorld(",
    """function fitRelationView(): void {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect || !relationFocusModelId.value) return

  const models = relationVisibleModels.value
  if (models.length === 0) return

  const minX = Math.min(...models.map((model) => relationModelX(model)))
  const minY = Math.min(...models.map((model) => relationModelY(model)))
  const maxX = Math.max(
    ...models.map((model) => relationModelX(model) + model.width),
  )
  const maxY = Math.max(
    ...models.map((model) => relationModelY(model) + relationNodeHeight(model)),
  )
  const width = Math.max(1, maxX - minX)
  const height = Math.max(1, maxY - minY)
  const padding = 150
  const nextZoom = clamp(
    Math.min(
      (rect.width - padding * 2) / width,
      (rect.height - padding * 2) / height,
      1.18,
    ),
    props.minZoom,
    props.maxZoom,
  )

  zoom.value = nextZoom
  viewX.value = rect.width / 2 - (minX + width / 2) * nextZoom
  viewY.value = rect.height / 2 - (minY + height / 2) * nextZoom
}

""",
    "fit relation layout",
)

designer = replace_once(
    designer,
    """              :model="model"
              :x="modelX(model)"
              :y="modelY(model)"
              :selected="false"
""",
    """              :model="model"
              :x="relationModelX(model)"
              :y="relationModelY(model)"
              :selected="false"
""",
    "relation card layout coordinates",
)

designer_path.write_text(designer, encoding="utf-8")


# A final override sheet keeps the visual language minimal without disturbing editor forms.
style_path = ROOT / "src/styles/minimal-nodes.css"
style_path.write_text(
    '''.md-model-node {
  min-height: 0;
  height: var(--md-node-height, 110px);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--md-line) 88%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, var(--md-panel-solid) 96%, transparent);
  box-shadow: 0 8px 24px color-mix(in srgb, #18213a 9%, transparent);
}

.md-model-node:hover {
  border-color: color-mix(in srgb, var(--md-accent) 32%, var(--md-line));
  box-shadow: 0 10px 28px color-mix(in srgb, #18213a 12%, transparent);
}

.md-model-node.is-selected {
  border-color: color-mix(in srgb, var(--md-accent) 70%, var(--md-line));
  box-shadow:
    0 0 0 2px color-mix(in srgb, var(--md-accent) 12%, transparent),
    0 10px 28px color-mix(in srgb, #18213a 12%, transparent);
}

.md-model-node__accent,
.md-model-node__icon,
.md-model-node__signal,
.md-model-node__relation-context,
.md-model-node__footer {
  display: none !important;
}

.md-model-node__header {
  min-height: 48px;
  gap: 9px;
  padding: 0 11px;
  border-bottom: 0;
  cursor: grab;
}

.md-model-node.is-static .md-model-node__header {
  cursor: default;
}

.md-model-node__mark {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 3px;
  background: var(--md-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--md-accent) 10%, transparent);
}

.md-model-node__title {
  font-size: 13px;
  font-weight: 780;
  letter-spacing: -0.012em;
}

.md-model-node__code {
  margin-top: 1px;
  font-size: 8px;
  letter-spacing: 0.04em;
}

.md-model-node__menu {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  opacity: 0.38;
}

.md-model-node:hover .md-model-node__menu,
.md-model-node.is-selected .md-model-node__menu {
  opacity: 0.72;
}

.md-model-node__purpose {
  display: flex;
  min-height: 32px;
  align-items: center;
  margin: 0;
  padding: 0 11px;
  border-top: 1px solid color-mix(in srgb, var(--md-line) 68%, transparent);
  border-bottom: 0;
  color: var(--md-muted);
  font-size: 9px;
  line-height: 1.4;
  white-space: nowrap;
}

.md-model-node__meta {
  display: flex;
  min-height: 30px;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 11px;
  border-top: 1px solid color-mix(in srgb, var(--md-line) 68%, transparent);
}

.md-model-node__tag-list {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 4px;
  overflow: hidden;
}

.md-model-node__meta .md-model-node__tag {
  max-width: 62px;
  padding: 2px 6px;
  border: 0;
  border-radius: 6px;
  color: var(--md-muted);
  background: var(--md-surface);
  font-size: 7px;
  font-weight: 680;
}

.md-model-node__meta .md-model-node__tag.is-more,
.md-model-node__tag-empty {
  color: var(--md-faint);
  font-size: 7px;
}

.md-model-node__metrics {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 6px;
}

.md-model-node__metrics b {
  color: var(--md-faint);
  font-size: 7px;
  font-weight: 720;
}

.md-relation-stage .md-model-node.is-relation-card {
  overflow: hidden;
  border-color: color-mix(in srgb, var(--md-accent) 28%, var(--md-line));
  border-radius: 13px;
  background: color-mix(in srgb, var(--md-panel-solid) 92%, transparent);
  box-shadow:
    0 18px 48px color-mix(in srgb, #172038 16%, transparent),
    0 0 28px color-mix(in srgb, var(--md-accent) 10%, transparent);
}

.md-relation-stage .md-model-node.is-relation-card::before,
.md-relation-stage .md-model-node.is-relation-card::after {
  display: none;
}

.md-relation-stage .md-model-node.is-relation-focus {
  border-color: color-mix(in srgb, var(--md-accent) 68%, var(--md-line));
  box-shadow:
    0 20px 54px color-mix(in srgb, #172038 18%, transparent),
    0 0 0 2px color-mix(in srgb, var(--md-accent) 12%, transparent),
    0 0 34px color-mix(in srgb, var(--md-accent) 18%, transparent);
  animation:
    md-relation-node-enter 0.66s var(--md-relation-delay) cubic-bezier(0.16, 1, 0.3, 1) forwards,
    md-minimal-focus-pulse 3.8s calc(var(--md-relation-delay) + 0.75s) ease-in-out infinite;
}

.md-relation-stage .md-model-node.is-relation-related {
  border-color: color-mix(in srgb, var(--md-accent) 24%, var(--md-line));
}

.md-relation-stage .md-model-node__header {
  min-height: 50px;
  padding: 0 12px;
  border-bottom: 1px solid color-mix(in srgb, var(--md-line) 74%, transparent);
  background: transparent;
}

.md-model-node__role {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 5px;
  padding: 4px 7px;
  border: 1px solid color-mix(in srgb, var(--md-accent) 20%, var(--md-line));
  border-radius: 999px;
  color: var(--md-muted);
  background: color-mix(in srgb, var(--md-surface) 76%, transparent);
  font-size: 7px;
  font-weight: 760;
}

.md-model-node__role i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--md-success);
  box-shadow: 0 0 8px color-mix(in srgb, var(--md-success) 70%, transparent);
}

.md-model-node__role b {
  color: var(--md-text);
  font-size: 7px;
}

.md-relation-stage .md-model-node__fields {
  display: block;
  min-height: 0;
  padding: 8px 10px;
  overflow: hidden;
  background: color-mix(in srgb, var(--md-surface) 48%, transparent);
}

.md-relation-stage .md-model-node__field {
  min-height: 38px;
  padding: 0 2px;
  border-bottom-color: color-mix(in srgb, var(--md-line) 66%, transparent);
}

.md-relation-stage .md-model-node__field:last-child {
  border-bottom: 0;
}

.md-model-node__field-copy strong {
  font-size: 9px;
  font-weight: 720;
}

.md-model-node__field-copy small {
  font-size: 7px;
}

.md-relation-stage .md-model-node__field code {
  padding: 2px 6px;
  border: 0;
  background: color-mix(in srgb, var(--md-accent-soft) 58%, var(--md-panel-solid));
  font-size: 8px;
}

.md-relation-stage .md-model-node__empty {
  min-height: 46px;
  color: var(--md-faint);
  font-size: 8px;
}

.md-relation-stage .md-relation-line__halo {
  stroke-width: 7px;
  opacity: 0.7;
}

.md-relation-stage .md-relation-line__beam {
  stroke-width: 4px;
  opacity: 0.22;
}

.md-relation-stage .md-relation-line__path {
  stroke-width: 1.8px;
  stroke-dasharray: 8 6;
}

.md-relation-stage .md-relation-line__label rect {
  fill: color-mix(in srgb, var(--md-panel-solid) 94%, transparent);
  stroke: color-mix(in srgb, var(--md-accent) 28%, var(--md-line));
  filter: drop-shadow(0 5px 12px color-mix(in srgb, #000 12%, transparent));
}

.md-relation-stage .md-relation-line__label text {
  font-size: 8px;
  font-weight: 720;
}

.md-canvas.is-relation-stage .md-canvas__tips,
.md-canvas.is-relation-stage .md-zoom-control {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

@keyframes md-minimal-focus-pulse {
  0%, 100% {
    box-shadow:
      0 20px 54px color-mix(in srgb, #172038 18%, transparent),
      0 0 0 2px color-mix(in srgb, var(--md-accent) 10%, transparent),
      0 0 28px color-mix(in srgb, var(--md-accent) 14%, transparent);
  }
  50% {
    box-shadow:
      0 22px 58px color-mix(in srgb, #172038 20%, transparent),
      0 0 0 2px color-mix(in srgb, var(--md-accent) 16%, transparent),
      0 0 40px color-mix(in srgb, var(--md-accent) 22%, transparent);
  }
}
''',
    encoding="utf-8",
)

index_style_path = ROOT / "src/styles/index.css"
index_style = index_style_path.read_text(encoding="utf-8")
if "@import './minimal-nodes.css';" not in index_style:
    index_style = index_style.rstrip() + "\n@import './minimal-nodes.css';\n"
index_style_path.write_text(index_style, encoding="utf-8")


# Lock the new geometry in a regression test.
test_path = ROOT / "tests/document.test.ts"
tests = test_path.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    """  modelHeight,
  normalizeDocument,
""",
    """  modelHeight,
  normalizeDocument,
  relationModelHeight,
""",
    "relation height test import",
)
insert_marker = "describe('model design document', () => {\n"
tests = replace_once(
    tests,
    insert_marker,
    insert_marker
    + """  it('keeps normal nodes compact and relation cards field-sized', () => {
    const model = createModel({
      fields: Array.from({ length: 24 }, (_, index) => ({
        name: `字段 ${index + 1}`,
      })),
    })

    expect(modelHeight(model)).toBe(110)
    expect(relationModelHeight(model, 0)).toBe(112)
    expect(relationModelHeight(model, 1)).toBe(104)
    expect(relationModelHeight(model, 4)).toBe(218)
  })

""",
    "compact geometry regression test",
)
test_path.write_text(tests, encoding="utf-8")

print('Minimal cards and field-anchored relation layout applied')
