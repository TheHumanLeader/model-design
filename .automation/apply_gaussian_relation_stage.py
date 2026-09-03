from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# Compact canvas geometry; expanded relation cards use their own height model.
core_path = ROOT / "src/core/document.ts"
core = core_path.read_text(encoding="utf-8")
core = replace_once(
    core,
    """export function modelHeight(model: ModelNode): number {
  const visibleFieldCount = Math.min(model.fields.length, 4)
  const tagHeight = (model.tags?.length ?? 0) > 0 ? 34 : 0
  const fieldAreaHeight =
    visibleFieldCount === 0
      ? 41
      : 12 +
        visibleFieldCount * 31 +
        (model.fields.length > 4 ? 34 : 0)

  return 58 + 43 + tagHeight + fieldAreaHeight + 25
}
""",
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
    "compact and relation model heights",
)
core_path.write_text(core, encoding="utf-8")


designer_path = ROOT / "src/components/ModelDesigner.vue"
designer = designer_path.read_text(encoding="utf-8")

designer = replace_once(
    designer,
    """  modelHeight,
  nextName,
""",
    """  modelHeight,
  relationModelHeight,
  nextName,
""",
    "relation model height import",
)

designer = replace_once(
    designer,
    """interface RelationLine {
  id: string
  path: string
  label: string
  labelX: number
  labelY: number
  labelWidth: number
}
""",
    """interface RelationLine {
  id: string
  path: string
  label: string
  labelX: number
  labelY: number
  labelWidth: number
  startX: number
  startY: number
  endX: number
  endY: number
}
""",
    "relation line terminals",
)

designer = replace_once(
    designer,
    """const relationFocusModelId = ref<string | null>(null)
const past = shallowRef<HistoryEntry[]>([])
""",
    """const relationFocusModelId = ref<string | null>(null)
const relationPreviousView = shallowRef<{
  x: number
  y: number
  zoom: number
} | null>(null)
const past = shallowRef<HistoryEntry[]>([])
""",
    "relation previous viewport",
)

designer = replace_once(
    designer,
    """const rootClass = computed(() => ({
  'md-model-designer--readonly': props.readonly,
  'md-model-designer--without-toolbar': !props.showToolbar,
  'md-model-designer--without-status': !props.showStatusBar,
  'md-model-designer--without-inspector': !props.showInspector,
}))
""",
    """const rootClass = computed(() => ({
  'md-model-designer--readonly': props.readonly,
  'md-model-designer--without-toolbar': !props.showToolbar,
  'md-model-designer--without-status': !props.showStatusBar,
  'md-model-designer--without-inspector': !props.showInspector,
  'md-model-designer--relation-view': Boolean(relationFocusModelId.value),
}))
""",
    "relation root class",
)

designer = replace_once(
    designer,
    """const relationVisibleModelIds = computed(() => {
  const ids = new Set<string>()
  const modelId = relationFocusModelId.value
  if (!modelId) return ids

  ids.add(modelId)
  focusedRelationEdges.value.forEach((edge) => {
    ids.add(edge.sourceModelId)
    ids.add(edge.targetModelId)
  })
  return ids
})
const relationLines = computed<RelationLine[]>(() =>
""",
    """const relationVisibleModelIds = computed(() => {
  const ids = new Set<string>()
  const modelId = relationFocusModelId.value
  if (!modelId) return ids

  ids.add(modelId)
  focusedRelationEdges.value.forEach((edge) => {
    ids.add(edge.sourceModelId)
    ids.add(edge.targetModelId)
  })
  return ids
})
const relationVisibleModels = computed(() => {
  const focusId = relationFocusModelId.value
  return designDocument.value.models
    .filter((model) => relationVisibleModelIds.value.has(model.id))
    .sort((left, right) => {
      if (left.id === focusId) return -1
      if (right.id === focusId) return 1
      return left.name.localeCompare(right.name, 'zh-CN')
    })
})
const relationFieldIdsByModelId = computed(() => {
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
    "relation visible models and fields",
)

designer = replace_once(
    designer,
    """  if (menu.target === 'canvas') {
    const items: DesignerMenuItem[] = [
""",
    """  if (menu.target === 'canvas') {
    if (relationViewActive.value) {
      return [
        {
          id: 'clear-relation-view',
          label: '退出关系视图',
          hint: 'Esc',
        },
        {
          id: 'fit-relation-view',
          label: '重新聚焦关系网络',
          separatorBefore: true,
        },
      ]
    }

    const items: DesignerMenuItem[] = [
""",
    "relation canvas menu",
)

designer = replace_once(
    designer,
    """function viewRelations(modelId: string): void {
  const model = designDocument.value.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  relationFocusModelId.value = modelId
  setModelSelection([modelId])
  closeMenu()

  const count = relationEdges.value.filter(
    (edge) => edge.sourceModelId === modelId || edge.targetModelId === modelId,
  ).length
  notify(count > 0 ? `已展示 ${count} 条模型关系` : '该模型暂无字段关系')
  void nextTick(() => fitRelationView())
}

function clearRelationView(): void {
  if (!relationFocusModelId.value) return

  relationFocusModelId.value = null
  notify('已退出关系查看')
}
""",
    """function viewRelations(modelId: string): void {
  const model = designDocument.value.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  if (!relationViewActive.value) {
    relationPreviousView.value = {
      x: viewX.value,
      y: viewY.value,
      zoom: zoom.value,
    }
  }

  relationFocusModelId.value = modelId
  setModelSelection([modelId])
  closeMenu()
  cancelGesture()

  const count = relationEdges.value.filter(
    (edge) => edge.sourceModelId === modelId || edge.targetModelId === modelId,
  ).length
  notify(count > 0 ? `已进入关系图层 · ${count} 条直接关系` : '已进入关系图层 · 暂无直接关系')
  void nextTick(() => fitRelationView())
}

function clearRelationView(): void {
  if (!relationFocusModelId.value) return

  const previousView = relationPreviousView.value
  relationFocusModelId.value = null
  relationPreviousView.value = null
  closeMenu()
  notify('已退出关系图层')

  if (previousView) {
    requestAnimationFrame(() => {
      viewX.value = previousView.x
      viewY.value = previousView.y
      zoom.value = previousView.zoom
    })
  }
}
""",
    "relation view lifecycle",
)

designer = replace_once(
    designer,
    """function modelRelationCount(modelId: string): number {
  return relationCountByModelId.value.get(modelId) ?? 0
}

function groupRelationState(
""",
    """function modelRelationCount(modelId: string): number {
  return relationCountByModelId.value.get(modelId) ?? 0
}

function relationFieldIds(modelId: string): string[] {
  return [...(relationFieldIdsByModelId.value.get(modelId) ?? [])]
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

function groupRelationState(
""",
    "relation node helpers",
)

designer = replace_once(
    designer,
    """    width: source.width,
    height: modelHeight(source),
  }
  const targetRect = {
    x: modelX(target),
    y: modelY(target),
    width: target.width,
    height: modelHeight(target),
""",
    """    width: source.width,
    height: relationNodeHeight(source),
  }
  const targetRect = {
    x: modelX(target),
    y: modelY(target),
    width: target.width,
    height: relationNodeHeight(target),
""",
    "relation line node heights",
)

designer = replace_once(
    designer,
    """      labelX: loopX - 10,
      labelY: (startY + endY) / 2,
      labelWidth,
    }
""",
    """      labelX: loopX - 10,
      labelY: (startY + endY) / 2,
      labelWidth,
      startX,
      startY,
      endX: startX,
      endY,
    }
""",
    "self relation terminals",
)

designer = replace_once(
    designer,
    """    labelX,
    labelY,
    labelWidth,
  }
}
""",
    """    labelX,
    labelY,
    labelWidth,
    startX,
    startY,
    endX,
    endY,
  }
}
""",
    "normal relation terminals",
)

designer = replace_once(
    designer,
    """function startModelDrag(modelId: string, event: PointerEvent): void {
  if (event.button !== 0) return
""",
    """function startModelDrag(modelId: string, event: PointerEvent): void {
  if (event.button !== 0 || relationViewActive.value) return
""",
    "disable model drag in relation stage",
)

designer = replace_once(
    designer,
    """  if (event.button === 0) {
    closeMenu()
    clearSelection()
    rootRef.value?.focus({ preventScroll: true })
  }
}
""",
    """  if (event.button === 0) {
    closeMenu()
    if (!relationViewActive.value) {
      clearSelection()
    }
    rootRef.value?.focus({ preventScroll: true })
  }
}
""",
    "preserve relation focus on canvas click",
)

designer = replace_once(
    designer,
    """  const maxY = Math.max(...models.map((model) => model.y + modelHeight(model)))
  const width = Math.max(1, maxX - minX)
  const height = Math.max(1, maxY - minY)
  const padding = 110
""",
    """  const maxY = Math.max(...models.map((model) => model.y + relationNodeHeight(model)))
  const width = Math.max(1, maxX - minX)
  const height = Math.max(1, maxY - minY)
  const padding = 138
""",
    "fit relation card heights",
)

designer = replace_once(
    designer,
    """    case 'clear-relation-view':
      clearRelationView()
      break
""",
    """    case 'clear-relation-view':
      clearRelationView()
      break
    case 'fit-relation-view':
      fitRelationView()
      break
""",
    "fit relation menu action",
)

designer = replace_once(
    designer,
    """function handleCanvasDoubleClick(event: MouseEvent): void {
  if (props.readonly || spacePressed.value) return
""",
    """function handleCanvasDoubleClick(event: MouseEvent): void {
  if (props.readonly || spacePressed.value || relationViewActive.value) return
""",
    "disable create in relation stage",
)

designer = replace_once(
    designer,
    """        :class="{
          'is-panning': gesture?.kind === 'pan',
          'is-space-ready': spacePressed && !gesture,
        }"
""",
    """        :class="{
          'is-panning': gesture?.kind === 'pan',
          'is-space-ready': spacePressed && !gesture,
          'is-relation-stage': relationViewActive,
        }"
""",
    "relation canvas class",
)

designer = replace_once(
    designer,
    """          <ModelRelations
            v-if="relationViewActive"
            :lines="relationLines"
          />

""",
    "",
    "remove relation lines from base world",
)

designer = replace_once(
    designer,
    """        <div v-if="relationFocusModel" class="md-relation-view-bar">
          <span class="md-relation-view-bar__icon" aria-hidden="true">↗</span>
          <span>
            <strong>{{ relationFocusModel.name }}</strong>
            <small>
              {{
                focusedRelationEdges.length
                  ? `${focusedRelationEdges.length} 条直接关系`
                  : '暂无字段关系'
              }}
            </small>
          </span>
          <button type="button" @click="clearRelationView">退出关系查看</button>
        </div>
""",
    """        <div v-if="relationFocusModel" class="md-relation-stage">
          <div class="md-relation-stage__backdrop"></div>
          <div class="md-relation-stage__grid"></div>
          <div class="md-relation-stage__scan"></div>

          <div class="md-relation-stage__world" :style="worldStyle">
            <ModelRelations :lines="relationLines" />

            <ModelNodeView
              v-for="model in relationVisibleModels"
              :key="`relation:${model.id}`"
              :model="model"
              :x="modelX(model)"
              :y="modelY(model)"
              :selected="false"
              :dragging="false"
              :relation-state="modelRelationState(model.id)"
              :relation-count="modelRelationCount(model.id)"
              :detail="true"
              :detail-field-ids="relationFieldIds(model.id)"
              :appearance-index="relationNodeIndex(model.id)"
              :interactive="false"
            />
          </div>

          <div class="md-relation-stage__hud">
            <span class="md-relation-stage__mode"><i></i> RELATION LAYER</span>
            <span class="md-relation-stage__title">
              <strong>{{ relationFocusModel.name }} · 关系网络</strong>
              <small>高斯景深图层 · 仅展示直接关联模型和参与关系的字段</small>
            </span>
            <span class="md-relation-stage__stats">
              <span><b>{{ relationVisibleModels.length }}</b> 模型</span>
              <span><b>{{ focusedRelationEdges.length }}</b> 关系</span>
            </span>
            <button class="md-relation-stage__exit" type="button" @click="clearRelationView">
              <kbd>Esc</kbd>
              退出图层
            </button>
          </div>

          <div class="md-relation-stage__legend">
            <span><i></i> 关系源</span>
            <span><i></i> 数据流向</span>
          </div>
        </div>
""",
    "gaussian relation stage template",
)

designer_path.write_text(designer, encoding="utf-8")


# Keep a geometry regression test so the compact node never silently grows fields again.
test_path = ROOT / "tests/document.test.ts"
tests = test_path.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    """  modelHeight,
  normalizeDocument,
""",
    """  modelHeight,
  relationModelHeight,
  normalizeDocument,
""",
    "relation height test import",
)
tests = replace_once(
    tests,
    """  it('creates event signatures and trigger defaults', () => {
""",
    """  it('keeps canvas nodes compact and expands only relation cards', () => {
    const model = createModel({
      name: '订单',
      tags: ['交易'],
      fields: Array.from({ length: 20 }, (_, index) => ({
        name: `字段 ${index + 1}`,
      })),
    })

    const compactHeight = modelHeight(model)
    const relationHeight = relationModelHeight(model, 4)

    expect(compactHeight).toBe(160)
    expect(relationHeight).toBeGreaterThan(compactHeight)
    expect(modelHeight({ ...model, fields: [] })).toBe(compactHeight)
  })

  it('creates event signatures and trigger defaults', () => {
""",
    "compact node regression test",
)
test_path.write_text(tests, encoding="utf-8")

print("Gaussian relation stage migration applied")
