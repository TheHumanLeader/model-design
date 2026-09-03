<script setup lang="ts" vapor>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  shallowRef,
  watch,
} from 'vue'
import DesignerContextMenu from './DesignerContextMenu.vue'
import ModelGroupView from './ModelGroup.vue'
import ModelInspector from './ModelInspector.vue'
import ModelNodeView from './ModelNode.vue'
import ModelRelations from './ModelRelations.vue'
import {
  DEFAULT_GRID_SIZE,
  GROUP_CONTENT_TOP,
  GROUP_HEADER_HEIGHT,
  GROUP_PADDING,
  MIN_GROUP_HEIGHT,
  MIN_GROUP_WIDTH,
  MODEL_NODE_BASE_HEIGHT,
  cloneDocument,
  constrainModelMovement,
  createEmptyDocument,
  createEventParameter,
  createField,
  createGroup,
  createGroupAroundModels,
  createModel,
  createModelEvent,
  createModelTrigger,
  findFreeModelPosition,
  fitGroupToContents,
  getDocumentBounds,
  isSameDocument,
  modelHeight,
  relationModelHeight,
  nextName,
  normalizeCode,
  normalizeDocument,
  snap,
} from '../core'
import { MODEL_RELATION_TYPE_LABELS } from '../types'
import type {
  DesignerMenuItem,
  DesignerSelection,
  EventParameterPatch,
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelDesignerApi,
  ModelEventPatch,
  ModelField,
  ModelFieldRelation,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelTriggerPatch,
  Point,
} from '../types'

type MenuTarget = 'canvas' | 'model' | 'group'

type Gesture =
  | {
      kind: 'pan'
      startClientX: number
      startClientY: number
      startViewX: number
      startViewY: number
    }
  | {
      kind: 'models'
      ids: string[]
      startClientX: number
      startClientY: number
    }
  | {
      kind: 'group'
      groupId: string
      startClientX: number
      startClientY: number
    }
  | {
      kind: 'resize-group'
      groupId: string
      startClientX: number
      startClientY: number
      startWidth: number
      startHeight: number
    }

interface MenuState {
  open: boolean
  target: MenuTarget
  id: string | null
  clientX: number
  clientY: number
  worldX: number
  worldY: number
}

interface HistoryEntry {
  document: ModelDesignDocument
  label: string
}

interface RelationEdge {
  id: string
  sourceModelId: string
  sourceField: ModelField
  targetModelId: string
  targetField: ModelField | null
  relation: ModelFieldRelation
}

interface RelationLine {
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

const props = withDefaults(
  defineProps<{
    readonly?: boolean
    height?: string | number
    showToolbar?: boolean
    showInspector?: boolean
    showStatusBar?: boolean
    gridSize?: number
    minZoom?: number
    maxZoom?: number
  }>(),
  {
    readonly: false,
    height: '100%',
    showToolbar: true,
    showInspector: true,
    showStatusBar: true,
    gridSize: DEFAULT_GRID_SIZE,
    minZoom: 0.25,
    maxZoom: 2.5,
  },
)

const designDocument = defineModel<ModelDesignDocument>({
  default: () => createEmptyDocument(),
})

const emit = defineEmits<{
  change: [document: ModelDesignDocument, label: string]
  selectionChange: [selection: DesignerSelection]
  ready: [api: ModelDesignerApi]
  error: [error: Error]
}>()

try {
  const normalizedInitialDocument = normalizeDocument(designDocument.value)
  if (!isSameDocument(designDocument.value, normalizedInitialDocument)) {
    designDocument.value = normalizedInitialDocument
  }
} catch (error) {
  const normalizedError =
    error instanceof Error ? error : new Error('初始模型设计文档无效')
  designDocument.value = createEmptyDocument()
  emit('error', normalizedError)
}

const rootRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLElement | null>(null)

const viewX = ref(150)
const viewY = ref(100)
const zoom = ref(1)
const selectedModelIds = shallowRef(new Set<string>())
const selectedGroupId = ref<string | null>(null)
const gesture = shallowRef<Gesture | null>(null)
const dragDeltaX = ref(0)
const dragDeltaY = ref(0)
const resizeWidth = ref(0)
const resizeHeight = ref(0)
const dropTargetGroupId = ref<string | null>(null)
const spacePressed = ref(false)
const toastMessage = ref('')
const relationFocusModelId = ref<string | null>(null)
const relationPreviousView = shallowRef<{
  x: number
  y: number
  zoom: number
} | null>(null)
const past = shallowRef<HistoryEntry[]>([])
const future = shallowRef<HistoryEntry[]>([])

let toastTimer: ReturnType<typeof setTimeout> | null = null
let lastMergeKey: string | null = null
let lastMergeAt = 0

const menu = reactive<MenuState>({
  open: false,
  target: 'canvas',
  id: null,
  clientX: 0,
  clientY: 0,
  worldX: 0,
  worldY: 0,
})

const rootStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
}))

const rootClass = computed(() => ({
  'md-model-designer--readonly': props.readonly,
  'md-model-designer--without-toolbar': !props.showToolbar,
  'md-model-designer--without-status': !props.showStatusBar,
  'md-model-designer--without-inspector': !props.showInspector,
  'md-model-designer--relation-view': Boolean(relationFocusModelId.value),
}))

const canvasStyle = computed(() => {
  const smallGrid = 24 * zoom.value
  const largeGrid = 120 * zoom.value

  return {
    backgroundSize: `${smallGrid}px ${smallGrid}px, ${smallGrid}px ${smallGrid}px, ${largeGrid}px ${largeGrid}px, ${largeGrid}px ${largeGrid}px`,
    backgroundPosition: `${viewX.value}px ${viewY.value}px`,
  }
})

const worldStyle = computed(() => ({
  transform: `translate3d(${viewX.value}px, ${viewY.value}px, 0) scale(${zoom.value})`,
}))

const zoomPercentage = computed(() => `${Math.round(zoom.value * 100)}%`)
const canUndo = computed(() => past.value.length > 0)
const canRedo = computed(() => future.value.length > 0)
const selectedModels = computed(() =>
  designDocument.value.models.filter((model) => selectedModelIds.value.has(model.id)),
)
const selectedGroup = computed(
  () =>
    designDocument.value.groups.find((group) => group.id === selectedGroupId.value) ?? null,
)
const selectedGroupMemberCount = computed(() => {
  const groupId = selectedGroupId.value
  return groupId
    ? designDocument.value.models.filter((model) => model.groupId === groupId).length
    : 0
})
const selectedCount = computed(
  () => selectedModelIds.value.size + (selectedGroupId.value ? 1 : 0),
)
const isEmpty = computed(
  () =>
    designDocument.value.models.length === 0 &&
    designDocument.value.groups.length === 0,
)
const relationEdges = computed<RelationEdge[]>(() => {
  const modelsById = new Map(
    designDocument.value.models.map((model) => [model.id, model]),
  )
  const edges: RelationEdge[] = []

  designDocument.value.models.forEach((sourceModel) => {
    sourceModel.fields.forEach((sourceField) => {
      const relation = sourceField.relation
      if (!relation) return

      const targetModel = modelsById.get(relation.modelId)
      if (!targetModel) return

      const targetField = relation.fieldId
        ? targetModel.fields.find((field) => field.id === relation.fieldId) ?? null
        : null

      edges.push({
        id: `${sourceModel.id}:${sourceField.id}`,
        sourceModelId: sourceModel.id,
        sourceField,
        targetModelId: targetModel.id,
        targetField,
        relation,
      })
    })
  })

  return edges
})
const relationCountByModelId = computed(() => {
  const counts = new Map<string, number>()

  relationEdges.value.forEach((edge) => {
    counts.set(edge.sourceModelId, (counts.get(edge.sourceModelId) ?? 0) + 1)
    if (edge.targetModelId !== edge.sourceModelId) {
      counts.set(edge.targetModelId, (counts.get(edge.targetModelId) ?? 0) + 1)
    }
  })

  return counts
})
const relationFocusModel = computed(() =>
  relationFocusModelId.value
    ? designDocument.value.models.find(
        (model) => model.id === relationFocusModelId.value,
      ) ?? null
    : null,
)
const focusedRelationEdges = computed(() => {
  const modelId = relationFocusModelId.value
  if (!modelId) return []

  return relationEdges.value.filter(
    (edge) =>
      edge.sourceModelId === modelId ||
      edge.targetModelId === modelId,
  )
})
const relationVisibleModelIds = computed(() => {
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
  focusedRelationEdges.value
    .map(createRelationLine)
    .filter((line): line is RelationLine => Boolean(line)),
)
const relationViewActive = computed(() => relationFocusModel.value !== null)

const menuItems = computed<DesignerMenuItem[]>(() => {
  if (menu.target === 'canvas') {
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
      { id: 'create-model', label: '创建模型', hint: '双击' },
      { id: 'create-group', label: '创建空分组' },
      {
        id: 'group-selected',
        label: '将所选模型组成分组',
        disabled: selectedModelIds.value.size === 0,
        separatorBefore: true,
      },
      { id: 'fit-view', label: '适配全部内容', separatorBefore: true },
    ]

    if (relationViewActive.value) {
      items.unshift({
        id: 'clear-relation-view',
        label: '退出关系查看',
        separatorBefore: false,
      })
      if (items[1]) items[1].separatorBefore = true
    }

    return items
  }

  if (menu.target === 'model') {
    const model = designDocument.value.models.find((candidate) => candidate.id === menu.id)
    const selectedIds = selectedModelIds.value.has(menu.id ?? '')
      ? [...selectedModelIds.value]
      : menu.id
        ? [menu.id]
        : []

    return [
      { id: 'configure-model', label: '配置模型' },
      {
        id:
          relationFocusModelId.value === model?.id
            ? 'clear-relation-view'
            : 'view-relations',
        label:
          relationFocusModelId.value === model?.id
            ? '退出关系查看'
            : '查看关系模型',
        separatorBefore: true,
      },
      {
        id: 'duplicate-model',
        label: selectedIds.length > 1 ? `复制所选 ${selectedIds.length} 个模型` : '复制模型',
        separatorBefore: true,
      },
      {
        id: 'group-selected',
        label: selectedIds.length > 1 ? '将所选模型组成分组' : '为模型创建分组',
        separatorBefore: true,
      },
      {
        id: 'remove-model-group',
        label: '移出当前分组',
        disabled: !model?.groupId,
      },
      {
        id: 'delete-model',
        label: selectedIds.length > 1 ? `删除所选 ${selectedIds.length} 个模型` : '删除模型',
        danger: true,
        separatorBefore: true,
      },
    ]
  }

  return [
    { id: 'create-model-in-group', label: '在分组中创建模型' },
    { id: 'fit-group', label: '适配分组内容', separatorBefore: true },
    { id: 'ungroup', label: '解散分组' },
    {
      id: 'delete-group',
      label: '删除分组',
      danger: true,
      separatorBefore: true,
    },
  ]
})

watch(
  () => designDocument.value,
  () => {
    cleanSelection()
    if (
      relationFocusModelId.value &&
      !designDocument.value.models.some(
        (model) => model.id === relationFocusModelId.value,
      )
    ) {
      relationFocusModelId.value = null
    }
  },
  { deep: false },
)

function commitDocument(
  next: ModelDesignDocument,
  label: string,
  mergeKey?: string,
): boolean {
  if (props.readonly || isSameDocument(designDocument.value, next)) {
    return false
  }

  const now = Date.now()
  const mergeWithPrevious =
    Boolean(mergeKey) &&
    mergeKey === lastMergeKey &&
    now - lastMergeAt < 850

  if (!mergeWithPrevious) {
    const entry: HistoryEntry = {
      document: cloneDocument(designDocument.value),
      label,
    }
    past.value = [...past.value.slice(-99), entry]
  }

  future.value = []
  designDocument.value = next
  lastMergeKey = mergeKey ?? null
  lastMergeAt = now
  emit('change', cloneDocument(next), label)
  notify(label)
  return true
}

function replaceDocument(
  next: ModelDesignDocument,
  label: string,
  recordHistory = true,
): void {
  if (recordHistory) {
    commitDocument(next, label)
    return
  }

  designDocument.value = next
  emit('change', cloneDocument(next), label)
  notify(label)
}

function resetMergeState(): void {
  lastMergeKey = null
  lastMergeAt = 0
}

function notify(message: string): void {
  toastMessage.value = message

  if (toastTimer) {
    clearTimeout(toastTimer)
  }

  toastTimer = setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, 1800)
}

function emitSelectionChange(): void {
  emit('selectionChange', {
    modelIds: [...selectedModelIds.value],
    groupId: selectedGroupId.value,
  })
}

function setModelSelection(ids: Iterable<string>): void {
  selectedModelIds.value = new Set(ids)
  selectedGroupId.value = null
  emitSelectionChange()
}

function setGroupSelection(groupId: string | null): void {
  selectedModelIds.value = new Set()
  selectedGroupId.value = groupId
  emitSelectionChange()
}

function clearSelection(): void {
  selectedModelIds.value = new Set()
  selectedGroupId.value = null
  emitSelectionChange()
}

function viewRelations(modelId: string): void {
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

function modelRelationState(
  modelId: string,
): 'none' | 'focus' | 'related' | 'dimmed' {
  const focusId = relationFocusModelId.value
  if (!focusId) return 'none'
  if (modelId === focusId) return 'focus'
  return relationVisibleModelIds.value.has(modelId) ? 'related' : 'dimmed'
}

function modelRelationCount(modelId: string): number {
  return relationCountByModelId.value.get(modelId) ?? 0
}

function relationFieldIds(modelId: string): string[] {
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

function groupRelationState(groupId: string): 'none' | 'context' | 'dimmed' {
  if (!relationFocusModelId.value) return 'none'

  const hasVisibleMember = designDocument.value.models.some(
    (model) =>
      model.groupId === groupId &&
      relationVisibleModelIds.value.has(model.id),
  )
  return hasVisibleMember ? 'context' : 'dimmed'
}

function cleanSelection(): void {
  const validModelIds = new Set(designDocument.value.models.map((model) => model.id))
  const nextModelIds = new Set(
    [...selectedModelIds.value].filter((id) => validModelIds.has(id)),
  )
  const validGroup =
    selectedGroupId.value &&
    designDocument.value.groups.some((group) => group.id === selectedGroupId.value)
      ? selectedGroupId.value
      : null

  if (
    nextModelIds.size !== selectedModelIds.value.size ||
    validGroup !== selectedGroupId.value
  ) {
    selectedModelIds.value = nextModelIds
    selectedGroupId.value = validGroup
    emitSelectionChange()
  }
}

function selectModelForPointer(modelId: string, event: PointerEvent | MouseEvent): boolean {
  const additive = event.ctrlKey || event.metaKey || event.shiftKey
  const current = new Set(selectedModelIds.value)

  if (additive) {
    if (current.has(modelId)) {
      current.delete(modelId)
    } else {
      current.add(modelId)
    }

    setModelSelection(current)
    return current.has(modelId)
  }

  if (!current.has(modelId)) {
    setModelSelection([modelId])
  } else {
    selectedGroupId.value = null
  }

  return true
}

function getViewportCenter(): Point {
  const rect = canvasRef.value?.getBoundingClientRect()

  if (!rect) {
    return { x: 0, y: 0 }
  }

  return screenToWorld(rect.left + rect.width / 2, rect.top + rect.height / 2)
}

function createModelAt(
  position: Partial<Point> = {},
  groupId: string | null = null,
): string {
  if (props.readonly) return ''

  const center = getViewportCenter()
  const requestedPosition = {
    x: position.x ?? center.x - 135,
    y: position.y ?? center.y - MODEL_NODE_BASE_HEIGHT / 2,
  }
  const groupExists =
    groupId && designDocument.value.groups.some((group) => group.id === groupId)
      ? groupId
      : null
  const next = cloneDocument(designDocument.value)
  const freePosition = findFreeModelPosition(
    next,
    requestedPosition,
    groupExists,
    props.gridSize,
  )
  const name = nextName('模型', next.models.map((model) => model.name))
  const model = createModel({
    name,
    code: normalizeCode(name),
    x: freePosition.x,
    y: freePosition.y,
    groupId: groupExists,
  })

  next.models.push(model)
  commitDocument(next, '已创建模型')
  setModelSelection([model.id])
  return model.id
}

function createGroupAt(position: Partial<Point> = {}): string {
  if (props.readonly) return ''

  const center = getViewportCenter()
  const next = cloneDocument(designDocument.value)
  const name = nextName('分组', next.groups.map((group) => group.name))
  const group = createGroup({
    name,
    x: snap(position.x ?? center.x - 215, props.gridSize),
    y: snap(position.y ?? center.y - 150, props.gridSize),
  })

  next.groups.push(group)
  commitDocument(next, '已创建分组')
  setGroupSelection(group.id)
  return group.id
}

function groupModels(modelIds: string[]): string | null {
  if (props.readonly || modelIds.length === 0) return null

  const result = createGroupAroundModels(designDocument.value, modelIds)
  if (!result.group) return null

  commitDocument(result.document, '已将模型组成分组')
  setGroupSelection(result.group.id)
  return result.group.id
}

function groupSelected(): string | null {
  return groupModels([...selectedModelIds.value])
}

function addField(modelId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  const name = nextName('字段', model.fields.map((field) => field.name))
  model.fields.push(
    createField({
      name,
      code: normalizeCode(name, `field_${model.fields.length + 1}`),
      type: 'string',
    }),
  )

  commitDocument(next, '已添加字段')
}

function addModelEvent(modelId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  const name = nextName('事件', model.events.map((item) => item.name))
  model.events.push(
    createModelEvent({
      name,
      code: normalizeCode(name, `event_${model.events.length + 1}`),
      returnType: 'void',
    }),
  )

  commitDocument(next, '已添加事件')
}

function addEventParameter(modelId: string, eventId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const item = next.models
    .find((model) => model.id === modelId)
    ?.events.find((candidate) => candidate.id === eventId)
  if (!item) return

  const name = nextName('参数', item.parameters.map((parameter) => parameter.name))
  item.parameters.push(
    createEventParameter({
      name,
      type: 'unknown',
    }),
  )

  commitDocument(next, '已添加事件参数')
}

function addModelTrigger(modelId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  const name = nextName('触发器', model.triggers.map((item) => item.name))
  model.triggers.push(
    createModelTrigger({
      name,
      source: 'update',
      timing: 'after',
      eventId: model.events[0]?.id ?? null,
      enabled: true,
    }),
  )

  commitDocument(next, '已添加触发器')
}

function patchModelEvent(
  modelId: string,
  eventId: string,
  patch: ModelEventPatch,
  mergeKey?: string,
): void {
  const next = cloneDocument(designDocument.value)
  const item = next.models
    .find((model) => model.id === modelId)
    ?.events.find((candidate) => candidate.id === eventId)
  if (!item) return

  Object.assign(item, patch)
  commitDocument(next, '已更新事件', mergeKey)
}

function patchEventParameter(
  modelId: string,
  eventId: string,
  parameterId: string,
  patch: EventParameterPatch,
  mergeKey?: string,
): void {
  const next = cloneDocument(designDocument.value)
  const parameter = next.models
    .find((model) => model.id === modelId)
    ?.events.find((item) => item.id === eventId)
    ?.parameters.find((candidate) => candidate.id === parameterId)
  if (!parameter) return

  Object.assign(parameter, patch)
  commitDocument(next, '已更新事件参数', mergeKey)
}

function patchModelTrigger(
  modelId: string,
  triggerId: string,
  patch: ModelTriggerPatch,
  mergeKey?: string,
): void {
  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  const trigger = model?.triggers.find((candidate) => candidate.id === triggerId)
  if (!model || !trigger) return

  Object.assign(trigger, patch)

  if (trigger.source !== 'update' && trigger.source !== 'field-change') {
    trigger.fieldId = null
  } else if (
    trigger.fieldId &&
    !model.fields.some((field) => field.id === trigger.fieldId)
  ) {
    trigger.fieldId = null
  }

  if (
    trigger.eventId &&
    !model.events.some((item) => item.id === trigger.eventId)
  ) {
    trigger.eventId = null
  }

  commitDocument(next, '已更新触发器', mergeKey)
}

function deleteModelEvent(modelId: string, eventId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  const previousLength = model.events.length
  model.events = model.events.filter((item) => item.id !== eventId)
  if (model.events.length === previousLength) return

  model.triggers.forEach((trigger) => {
    if (trigger.eventId === eventId) trigger.eventId = null
  })
  commitDocument(next, '已删除事件')
}

function deleteEventParameter(
  modelId: string,
  eventId: string,
  parameterId: string,
): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const item = next.models
    .find((model) => model.id === modelId)
    ?.events.find((candidate) => candidate.id === eventId)
  if (!item) return

  const previousLength = item.parameters.length
  item.parameters = item.parameters.filter(
    (parameter) => parameter.id !== parameterId,
  )
  if (item.parameters.length === previousLength) return

  commitDocument(next, '已删除事件参数')
}

function deleteModelTrigger(modelId: string, triggerId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  const previousLength = model.triggers.length
  model.triggers = model.triggers.filter((item) => item.id !== triggerId)
  if (model.triggers.length === previousLength) return

  commitDocument(next, '已删除触发器')
}

function patchModel(modelId: string, patch: ModelPatch, mergeKey?: string): void {
  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  if (patch.name !== undefined) model.name = patch.name
  if (patch.code !== undefined) model.code = patch.code
  if (patch.purpose !== undefined) model.purpose = patch.purpose
  if (patch.tags !== undefined) model.tags = normalizeModelTags(patch.tags)

  if (patch.groupId !== undefined) {
    const group = patch.groupId
      ? next.groups.find((candidate) => candidate.id === patch.groupId) ?? null
      : null

    model.groupId = group?.id ?? null

    if (group) {
      const minX = group.x + GROUP_PADDING
      const minY = group.y + GROUP_CONTENT_TOP
      const maxX = Math.max(
        minX,
        group.x + group.width - GROUP_PADDING - model.width,
      )
      const maxY = Math.max(
        minY,
        group.y + group.height - GROUP_PADDING - modelHeight(model),
      )

      model.x = clamp(model.x, minX, maxX)
      model.y = clamp(model.y, minY, maxY)
    }
  }

  commitDocument(next, '已更新模型', mergeKey)
}

function patchGroup(groupId: string, patch: GroupPatch, mergeKey?: string): void {
  const next = cloneDocument(designDocument.value)
  const group = next.groups.find((candidate) => candidate.id === groupId)
  if (!group) return

  Object.assign(group, patch)
  commitDocument(next, '已更新分组', mergeKey)
}

function patchField(
  modelId: string,
  fieldId: string,
  patch: FieldPatch,
  mergeKey?: string,
): void {
  const next = cloneDocument(designDocument.value)
  const field = next.models
    .find((model) => model.id === modelId)
    ?.fields.find((candidate) => candidate.id === fieldId)

  if (!field) return
  Object.assign(field, patch)
  if (field.relation) {
    const targetModel = next.models.find(
      (model) => model.id === field.relation?.modelId,
    )
    if (!targetModel) {
      field.relation = null
    } else if (
      field.relation.fieldId &&
      !targetModel.fields.some(
        (targetField) => targetField.id === field.relation?.fieldId,
      )
    ) {
      field.relation.fieldId = null
    }
  }
  commitDocument(next, '已更新字段', mergeKey)
}

function deleteField(modelId: string, fieldId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  const model = next.models.find((candidate) => candidate.id === modelId)
  if (!model) return

  model.fields = model.fields.filter((field) => field.id !== fieldId)
  model.triggers.forEach((trigger) => {
    if (trigger.fieldId === fieldId) trigger.fieldId = null
  })

  next.models.forEach((candidate) => {
    candidate.fields.forEach((field) => {
      if (
        field.relation?.modelId === modelId &&
        field.relation.fieldId === fieldId
      ) {
        field.relation.fieldId = null
      }
    })
  })
  commitDocument(next, '已删除字段')
}

function duplicateModels(modelIds: string[]): string[] {
  if (props.readonly) return []

  const idSet = new Set(modelIds)
  const sourceModels = designDocument.value.models.filter((model) => idSet.has(model.id))
  if (sourceModels.length === 0) return []

  const next = cloneDocument(designDocument.value)
  const createdIds: string[] = []
  const modelIdMap = new Map<string, string>()
  const fieldIdMaps = new Map<string, Map<string, string>>()
  const eventIdMaps = new Map<string, Map<string, string>>()
  const copies: Array<{ source: ModelNode; copy: ModelNode }> = []

  sourceModels.forEach((source, index) => {
    const position = findFreeModelPosition(
      next,
      {
        x: source.x + 30 + index * 12,
        y: source.y + 30 + index * 12,
      },
      source.groupId,
      props.gridSize,
    )
    const copy = createModel({
      ...source,
      id: undefined,
      name: nextName(`${source.name} 副本`, next.models.map((model) => model.name)),
      x: position.x,
      y: position.y,
      fields: source.fields.map((field) => ({
        ...field,
        id: undefined,
      })),
      events: source.events.map((item) => ({
        ...item,
        id: undefined,
        parameters: item.parameters.map((parameter) => ({
          ...parameter,
          id: undefined,
        })),
      })),
      triggers: source.triggers.map((trigger) => ({
        ...trigger,
        id: undefined,
        fieldId: null,
        eventId: null,
      })),
    })
    const fieldIdMap = new Map<string, string>()
    const eventIdMap = new Map<string, string>()

    source.fields.forEach((field, fieldIndex) => {
      const copiedField = copy.fields[fieldIndex]
      if (copiedField) fieldIdMap.set(field.id, copiedField.id)
    })
    source.events.forEach((item, eventIndex) => {
      const copiedEvent = copy.events[eventIndex]
      if (copiedEvent) eventIdMap.set(item.id, copiedEvent.id)
    })

    next.models.push(copy)
    createdIds.push(copy.id)
    modelIdMap.set(source.id, copy.id)
    fieldIdMaps.set(source.id, fieldIdMap)
    eventIdMaps.set(source.id, eventIdMap)
    copies.push({ source, copy })
  })

  copies.forEach(({ source, copy }) => {
    source.fields.forEach((sourceField, fieldIndex) => {
      const copiedField = copy.fields[fieldIndex]
      const relation = copiedField?.relation
      const sourceRelation = sourceField.relation
      if (!copiedField || !relation || !sourceRelation) return

      const copiedTargetModelId = modelIdMap.get(sourceRelation.modelId)
      if (!copiedTargetModelId) return

      relation.modelId = copiedTargetModelId
      relation.fieldId = sourceRelation.fieldId
        ? fieldIdMaps.get(sourceRelation.modelId)?.get(sourceRelation.fieldId) ?? null
        : null
    })

    source.triggers.forEach((sourceTrigger, triggerIndex) => {
      const copiedTrigger = copy.triggers[triggerIndex]
      if (!copiedTrigger) return

      copiedTrigger.fieldId = sourceTrigger.fieldId
        ? fieldIdMaps.get(source.id)?.get(sourceTrigger.fieldId) ?? null
        : null
      copiedTrigger.eventId = sourceTrigger.eventId
        ? eventIdMaps.get(source.id)?.get(sourceTrigger.eventId) ?? null
        : null
    })
  })

  commitDocument(next, `已复制 ${createdIds.length} 个模型`)
  setModelSelection(createdIds)
  return createdIds
}

function deleteModels(modelIds: string[]): void {
  if (props.readonly || modelIds.length === 0) return

  const idSet = new Set(modelIds)
  const next = cloneDocument(designDocument.value)
  const removedCount = next.models.filter((model) => idSet.has(model.id)).length
  next.models = next.models.filter((model) => !idSet.has(model.id))
  next.models.forEach((model) => {
    model.fields.forEach((field) => {
      if (field.relation && idSet.has(field.relation.modelId)) {
        field.relation = null
      }
    })
  })

  if (removedCount === 0) return

  commitDocument(next, `已删除 ${removedCount} 个模型`)
  clearSelection()
}

function deleteGroup(groupId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  if (!next.groups.some((group) => group.id === groupId)) return

  next.groups = next.groups.filter((group) => group.id !== groupId)
  next.models.forEach((model) => {
    if (model.groupId === groupId) model.groupId = null
  })

  commitDocument(next, '已删除分组，组内模型已保留')
  clearSelection()
}

function ungroup(groupId: string): void {
  if (props.readonly) return

  const next = cloneDocument(designDocument.value)
  if (!next.groups.some((group) => group.id === groupId)) return

  next.groups = next.groups.filter((group) => group.id !== groupId)
  next.models.forEach((model) => {
    if (model.groupId === groupId) model.groupId = null
  })

  commitDocument(next, '已解散分组')
  clearSelection()
}

function fitGroup(groupId: string): void {
  if (props.readonly) return

  const next = fitGroupToContents(designDocument.value, groupId)
  commitDocument(next, '已适配分组内容')
}

function deleteSelected(): void {
  if (selectedModelIds.value.size > 0) {
    deleteModels([...selectedModelIds.value])
    return
  }

  if (selectedGroupId.value) {
    deleteGroup(selectedGroupId.value)
  }
}

function undo(): void {
  const entries = [...past.value]
  const previous = entries.pop()
  if (!previous) return

  future.value = [
    ...future.value.slice(-99),
    {
      document: cloneDocument(designDocument.value),
      label: previous.label,
    },
  ]
  past.value = entries
  resetMergeState()
  replaceDocument(cloneDocument(previous.document), `撤销：${previous.label}`, false)
  cleanSelection()
}

function redo(): void {
  const entries = [...future.value]
  const nextEntry = entries.pop()
  if (!nextEntry) return

  past.value = [
    ...past.value.slice(-99),
    {
      document: cloneDocument(designDocument.value),
      label: nextEntry.label,
    },
  ]
  future.value = entries
  resetMergeState()
  replaceDocument(cloneDocument(nextEntry.document), `重做：${nextEntry.label}`, false)
  cleanSelection()
}

function modelX(model: ModelNode): number {
  const currentGesture = gesture.value

  if (
    currentGesture?.kind === 'models' &&
    currentGesture.ids.includes(model.id)
  ) {
    return model.x + dragDeltaX.value
  }

  if (
    currentGesture?.kind === 'group' &&
    model.groupId === currentGesture.groupId
  ) {
    return model.x + dragDeltaX.value
  }

  return model.x
}

function modelY(model: ModelNode): number {
  const currentGesture = gesture.value

  if (
    currentGesture?.kind === 'models' &&
    currentGesture.ids.includes(model.id)
  ) {
    return model.y + dragDeltaY.value
  }

  if (
    currentGesture?.kind === 'group' &&
    model.groupId === currentGesture.groupId
  ) {
    return model.y + dragDeltaY.value
  }

  return model.y
}

function groupX(group: ModelGroup): number {
  return gesture.value?.kind === 'group' && gesture.value.groupId === group.id
    ? group.x + dragDeltaX.value
    : group.x
}

function groupY(group: ModelGroup): number {
  return gesture.value?.kind === 'group' && gesture.value.groupId === group.id
    ? group.y + dragDeltaY.value
    : group.y
}

function groupWidth(group: ModelGroup): number {
  return gesture.value?.kind === 'resize-group' && gesture.value.groupId === group.id
    ? resizeWidth.value
    : group.width
}

function groupHeight(group: ModelGroup): number {
  return gesture.value?.kind === 'resize-group' && gesture.value.groupId === group.id
    ? resizeHeight.value
    : group.height
}

function createRelationLine(edge: RelationEdge): RelationLine | null {
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

function cubicPoint(
  start: number,
  control1: number,
  control2: number,
  end: number,
  t: number,
): number {
  const inverse = 1 - t
  return (
    inverse ** 3 * start +
    3 * inverse ** 2 * t * control1 +
    3 * inverse * t ** 2 * control2 +
    t ** 3 * end
  )
}

function isModelDragging(modelId: string): boolean {
  const currentGesture = gesture.value
  return (
    currentGesture?.kind === 'models' &&
    currentGesture.ids.includes(modelId)
  )
}

function isGroupMoving(groupId: string): boolean {
  return gesture.value?.kind === 'group' && gesture.value.groupId === groupId
}

function isGroupResizing(groupId: string): boolean {
  return (
    gesture.value?.kind === 'resize-group' &&
    gesture.value.groupId === groupId
  )
}

function startModelDrag(modelId: string, event: PointerEvent): void {
  if (event.button !== 0 || relationViewActive.value) return

  const shouldDrag = selectModelForPointer(modelId, event)
  if (!shouldDrag || props.readonly) return

  event.preventDefault()
  closeMenu()
  resetMergeState()
  gesture.value = {
    kind: 'models',
    ids: [...selectedModelIds.value],
    startClientX: event.clientX,
    startClientY: event.clientY,
  }
  dragDeltaX.value = 0
  dragDeltaY.value = 0
  rootRef.value?.focus({ preventScroll: true })
}

function selectGroup(groupId: string, event: PointerEvent): void {
  if (event.button !== 0) return
  setGroupSelection(groupId)
  rootRef.value?.focus({ preventScroll: true })
}

function startGroupDrag(groupId: string, event: PointerEvent): void {
  if (event.button !== 0 || props.readonly) return

  event.preventDefault()
  setGroupSelection(groupId)
  closeMenu()
  resetMergeState()
  gesture.value = {
    kind: 'group',
    groupId,
    startClientX: event.clientX,
    startClientY: event.clientY,
  }
  dragDeltaX.value = 0
  dragDeltaY.value = 0
  rootRef.value?.focus({ preventScroll: true })
}

function startGroupResize(groupId: string, event: PointerEvent): void {
  if (event.button !== 0 || props.readonly) return

  const group = designDocument.value.groups.find((candidate) => candidate.id === groupId)
  if (!group) return

  event.preventDefault()
  setGroupSelection(groupId)
  closeMenu()
  resetMergeState()
  gesture.value = {
    kind: 'resize-group',
    groupId,
    startClientX: event.clientX,
    startClientY: event.clientY,
    startWidth: group.width,
    startHeight: group.height,
  }
  resizeWidth.value = group.width
  resizeHeight.value = group.height
  rootRef.value?.focus({ preventScroll: true })
}

function startPan(event: PointerEvent): void {
  event.preventDefault()
  closeMenu()
  gesture.value = {
    kind: 'pan',
    startClientX: event.clientX,
    startClientY: event.clientY,
    startViewX: viewX.value,
    startViewY: viewY.value,
  }
  rootRef.value?.focus({ preventScroll: true })
}

function handleCanvasPointerDown(event: PointerEvent): void {
  const wantsPan =
    event.button === 1 ||
    (event.button === 0 && spacePressed.value)

  if (wantsPan) {
    startPan(event)
    return
  }

  if (event.button === 0) {
    closeMenu()
    if (!relationViewActive.value) {
      clearSelection()
    }
    rootRef.value?.focus({ preventScroll: true })
  }
}

function handleGlobalPointerMove(event: PointerEvent): void {
  const currentGesture = gesture.value
  if (!currentGesture) return

  if (currentGesture.kind === 'pan') {
    viewX.value =
      currentGesture.startViewX + event.clientX - currentGesture.startClientX
    viewY.value =
      currentGesture.startViewY + event.clientY - currentGesture.startClientY
    return
  }

  const worldDeltaX = (event.clientX - currentGesture.startClientX) / zoom.value
  const worldDeltaY = (event.clientY - currentGesture.startClientY) / zoom.value

  if (currentGesture.kind === 'resize-group') {
    const group = designDocument.value.groups.find(
      (candidate) => candidate.id === currentGesture.groupId,
    )
    if (!group) return

    const members = designDocument.value.models.filter(
      (model) => model.groupId === currentGesture.groupId,
    )
    const minimumMemberWidth = members.length
      ? Math.max(
          MIN_GROUP_WIDTH,
          ...members.map((model) => model.x + model.width - group.x + 24),
        )
      : MIN_GROUP_WIDTH
    const minimumMemberHeight = members.length
      ? Math.max(
          MIN_GROUP_HEIGHT,
          ...members.map((model) => model.y + modelHeight(model) - group.y + 24),
        )
      : MIN_GROUP_HEIGHT

    resizeWidth.value = snap(
      Math.max(minimumMemberWidth, currentGesture.startWidth + worldDeltaX),
      props.gridSize,
    )
    resizeHeight.value = snap(
      Math.max(minimumMemberHeight, currentGesture.startHeight + worldDeltaY),
      props.gridSize,
    )
    return
  }

  const snappedDelta = {
    x: snap(worldDeltaX, props.gridSize),
    y: snap(worldDeltaY, props.gridSize),
  }
  const constrainedDelta =
    currentGesture.kind === 'models'
      ? constrainModelMovement(
          designDocument.value,
          currentGesture.ids,
          snappedDelta,
        )
      : snappedDelta

  dragDeltaX.value = constrainedDelta.x
  dragDeltaY.value = constrainedDelta.y

  if (currentGesture.kind === 'models') {
    updateDropTarget(currentGesture.ids)
  }
}

function finishGesture(): void {
  const currentGesture = gesture.value
  if (!currentGesture) return

  if (currentGesture.kind === 'models') {
    finishModelDrag(currentGesture)
  } else if (currentGesture.kind === 'group') {
    finishGroupDrag(currentGesture)
  } else if (currentGesture.kind === 'resize-group') {
    finishGroupResize(currentGesture)
  }

  cancelGesture()
}

function cancelGesture(): void {
  gesture.value = null
  dragDeltaX.value = 0
  dragDeltaY.value = 0
  resizeWidth.value = 0
  resizeHeight.value = 0
  dropTargetGroupId.value = null
}

function finishModelDrag(currentGesture: Extract<Gesture, { kind: 'models' }>): void {
  const dx = dragDeltaX.value
  const dy = dragDeltaY.value
  const targetGroupId = dropTargetGroupId.value
  if (dx === 0 && dy === 0) return

  const draggedModels = designDocument.value.models.filter((model) =>
    currentGesture.ids.includes(model.id),
  )
  const canEnterGroup = draggedModels.every((model) => !model.groupId)

  const next = cloneDocument(designDocument.value)
  next.models.forEach((model) => {
    if (!currentGesture.ids.includes(model.id)) return

    model.x += dx
    model.y += dy

    if (canEnterGroup && targetGroupId) {
      model.groupId = targetGroupId
    }
  })

  commitDocument(next, '已移动模型')
}

function finishGroupDrag(currentGesture: Extract<Gesture, { kind: 'group' }>): void {
  const dx = dragDeltaX.value
  const dy = dragDeltaY.value
  if (dx === 0 && dy === 0) return

  const next = cloneDocument(designDocument.value)
  const group = next.groups.find((candidate) => candidate.id === currentGesture.groupId)
  if (!group) return

  group.x += dx
  group.y += dy
  next.models.forEach((model) => {
    if (model.groupId === currentGesture.groupId) {
      model.x += dx
      model.y += dy
    }
  })

  commitDocument(next, '已移动分组')
}

function finishGroupResize(
  currentGesture: Extract<Gesture, { kind: 'resize-group' }>,
): void {
  const next = cloneDocument(designDocument.value)
  const group = next.groups.find((candidate) => candidate.id === currentGesture.groupId)
  if (!group) return

  group.width = resizeWidth.value
  group.height = resizeHeight.value
  commitDocument(next, '已调整分组大小')
}

function updateDropTarget(modelIds: string[]): void {
  const idSet = new Set(modelIds)
  const models = designDocument.value.models.filter((model) => idSet.has(model.id))

  if (
    models.length === 0 ||
    models.some((model) => model.groupId !== null)
  ) {
    dropTargetGroupId.value = null
    return
  }

  const minX = Math.min(...models.map((model) => model.x + dragDeltaX.value))
  const minY = Math.min(...models.map((model) => model.y + dragDeltaY.value))
  const maxX = Math.max(
    ...models.map((model) => model.x + dragDeltaX.value + model.width),
  )
  const maxY = Math.max(
    ...models.map(
      (model) => model.y + dragDeltaY.value + modelHeight(model),
    ),
  )

  const target =
    designDocument.value.groups
      .filter((group) => {
        const left = group.x + GROUP_PADDING
        const top = group.y + GROUP_CONTENT_TOP
        const right = group.x + group.width - GROUP_PADDING
        const bottom = group.y + group.height - GROUP_PADDING

        return minX >= left && minY >= top && maxX <= right && maxY <= bottom
      })
      .sort((left, right) => left.width * left.height - right.width * right.height)[0] ??
    null

  dropTargetGroupId.value = target?.id ?? null
}

function handleWheel(event: WheelEvent): void {
  event.preventDefault()

  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return

  const oldZoom = zoom.value
  const nextZoom = clamp(
    oldZoom * Math.exp(-event.deltaY * 0.0015),
    props.minZoom,
    props.maxZoom,
  )
  const worldX = (event.clientX - rect.left - viewX.value) / oldZoom
  const worldY = (event.clientY - rect.top - viewY.value) / oldZoom

  zoom.value = nextZoom
  viewX.value = event.clientX - rect.left - worldX * nextZoom
  viewY.value = event.clientY - rect.top - worldY * nextZoom
}

function setZoomAroundCanvasCenter(nextZoom: number): void {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return

  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  const oldZoom = zoom.value
  const clampedZoom = clamp(nextZoom, props.minZoom, props.maxZoom)
  const worldX = (centerX - rect.left - viewX.value) / oldZoom
  const worldY = (centerY - rect.top - viewY.value) / oldZoom

  zoom.value = clampedZoom
  viewX.value = centerX - rect.left - worldX * clampedZoom
  viewY.value = centerY - rect.top - worldY * clampedZoom
}

function zoomIn(): void {
  setZoomAroundCanvasCenter(zoom.value * 1.15)
}

function zoomOut(): void {
  setZoomAroundCanvasCenter(zoom.value / 1.15)
}

function resetZoom(): void {
  setZoomAroundCanvasCenter(1)
}

function fitView(): void {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return

  const bounds = getDocumentBounds(designDocument.value)
  if (!bounds) {
    zoom.value = 1
    viewX.value = rect.width / 2
    viewY.value = rect.height / 2
    return
  }

  const padding = 72
  const width = Math.max(bounds.width, 1)
  const height = Math.max(bounds.height, 1)
  const nextZoom = clamp(
    Math.min(
      (rect.width - padding * 2) / width,
      (rect.height - padding * 2) / height,
      1.2,
    ),
    props.minZoom,
    props.maxZoom,
  )

  zoom.value = nextZoom
  viewX.value = rect.width / 2 - (bounds.x + bounds.width / 2) * nextZoom
  viewY.value = rect.height / 2 - (bounds.y + bounds.height / 2) * nextZoom
}

function fitRelationView(): void {
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

function screenToWorld(clientX: number, clientY: number): Point {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return { x: 0, y: 0 }

  return {
    x: (clientX - rect.left - viewX.value) / zoom.value,
    y: (clientY - rect.top - viewY.value) / zoom.value,
  }
}

function openContextMenu(
  target: MenuTarget,
  id: string | null,
  event: MouseEvent,
): void {
  event.preventDefault()

  if (target === 'model' && id) {
    if (!selectedModelIds.value.has(id)) setModelSelection([id])
  } else if (target === 'group' && id) {
    setGroupSelection(id)
  }

  const point = screenToWorld(event.clientX, event.clientY)
  menu.open = true
  menu.target = target
  menu.id = id
  menu.clientX = Math.min(event.clientX, Math.max(8, window.innerWidth - 244))
  menu.clientY = Math.min(event.clientY, Math.max(8, window.innerHeight - 330))
  menu.worldX = point.x
  menu.worldY = point.y
  rootRef.value?.focus({ preventScroll: true })
}

function openCanvasMenu(event: MouseEvent): void {
  openContextMenu('canvas', null, event)
}

function openModelMenu(modelId: string, event: MouseEvent): void {
  openContextMenu('model', modelId, event)
}

function openGroupMenu(groupId: string, event: MouseEvent): void {
  openContextMenu('group', groupId, event)
}

function closeMenu(): void {
  menu.open = false
}

function handleMenuAction(action: string): void {
  const targetId = menu.id
  const target = menu.target
  const position = { x: menu.worldX, y: menu.worldY }
  closeMenu()

  switch (action) {
    case 'create-model':
      createModelAt(position)
      break
    case 'create-group':
      createGroupAt(position)
      break
    case 'create-model-in-group':
      if (targetId) createModelAt(position, targetId)
      break
    case 'configure-model':
      if (targetId) setModelSelection([targetId])
      break
    case 'view-relations':
      if (targetId) viewRelations(targetId)
      break
    case 'clear-relation-view':
      clearRelationView()
      break
    case 'fit-relation-view':
      fitRelationView()
      break
    case 'duplicate-model': {
      const ids =
        targetId && selectedModelIds.value.has(targetId)
          ? [...selectedModelIds.value]
          : targetId
            ? [targetId]
            : []
      duplicateModels(ids)
      break
    }
    case 'group-selected': {
      if (target === 'model' && targetId && !selectedModelIds.value.has(targetId)) {
        setModelSelection([targetId])
      }
      groupSelected()
      break
    }
    case 'remove-model-group':
      if (targetId) patchModel(targetId, { groupId: null })
      break
    case 'delete-model': {
      const ids =
        targetId && selectedModelIds.value.has(targetId)
          ? [...selectedModelIds.value]
          : targetId
            ? [targetId]
            : []
      deleteModels(ids)
      break
    }
    case 'fit-group':
      if (targetId) fitGroup(targetId)
      break
    case 'ungroup':
      if (targetId) ungroup(targetId)
      break
    case 'delete-group':
      if (targetId) deleteGroup(targetId)
      break
    case 'fit-view':
      fitView()
      break
  }
}

function handleCanvasDoubleClick(event: MouseEvent): void {
  if (props.readonly || spacePressed.value || relationViewActive.value) return
  createModelAt(screenToWorld(event.clientX, event.clientY))
}

function handleModelDoubleClick(modelId: string): void {
  setModelSelection([modelId])
}

function handleGroupDoubleClick(groupId: string): void {
  fitGroup(groupId)
}

function exportJSON(): string {
  return JSON.stringify(designDocument.value, null, 2)
}

function downloadJSON(): void {
  const blob = new Blob([exportJSON()], {
    type: 'application/json;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `model-design-${new Date().toISOString().slice(0, 10)}.json`
  anchor.click()
  URL.revokeObjectURL(url)
  notify('模型设计已导出为 JSON')
}

function importJSON(source: string): void {
  try {
    const parsed = JSON.parse(source) as unknown
    const next = normalizeDocument(parsed)
    commitDocument(next, '已导入模型设计')
    clearSelection()
    void nextTick(() => fitView())
  } catch (error) {
    const normalizedError =
      error instanceof Error ? error : new Error('无法导入模型设计')
    emit('error', normalizedError)
    notify(normalizedError.message)
    throw normalizedError
  }
}

function chooseImportFile(): void {
  if (props.readonly) return

  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,application/json'
  input.addEventListener(
    'change',
    () => {
      const file = input.files?.[0]
      if (!file) return

      void file
        .text()
        .then(importJSON)
        .catch((error: unknown) => {
          const normalizedError =
            error instanceof Error ? error : new Error('读取文件失败')
          emit('error', normalizedError)
          notify(normalizedError.message)
        })
    },
    { once: true },
  )
  input.click()
}

function getDocument(): ModelDesignDocument {
  return cloneDocument(designDocument.value)
}

function handleKeyDown(event: KeyboardEvent): void {
  if (isEditableTarget(event.target)) return

  if (event.key === ' ') {
    spacePressed.value = true
    event.preventDefault()
    return
  }

  if (event.key === 'Escape') {
    if (relationViewActive.value) {
      clearRelationView()
      closeMenu()
      cancelGesture()
      return
    }

    closeMenu()
    cancelGesture()
    clearSelection()
    return
  }

  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (!props.readonly && selectedCount.value > 0) {
      event.preventDefault()
      deleteSelected()
    }
    return
  }

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
    event.preventDefault()
    if (event.shiftKey) redo()
    else undo()
    return
  }

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') {
    event.preventDefault()
    redo()
  }
}

function handleKeyUp(event: KeyboardEvent): void {
  if (event.key === ' ') {
    spacePressed.value = false
  }
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false

  return (
    target.isContentEditable ||
    target.matches('input, textarea, select, [role="textbox"]')
  )
}

function normalizeModelTags(tags: string[] | undefined): string[] {
  const seen = new Set<string>()
  const normalized: string[] = []
  const source = tags ?? []

  source.forEach((item) => {
    const tag = item.trim().slice(0, 32)
    const key = tag.toLocaleLowerCase()
    if (!tag || seen.has(key)) return

    seen.add(key)
    normalized.push(tag)
  })

  return normalized.slice(0, 24)
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

const api: ModelDesignerApi = {
  createModel: createModelAt,
  createGroup: createGroupAt,
  groupSelected,
  deleteSelected,
  clearSelection,
  viewRelations,
  clearRelationView,
  undo,
  redo,
  fitView,
  zoomIn,
  zoomOut,
  exportJSON,
  importJSON,
  getDocument,
}

defineExpose(api)

onMounted(() => {
  try {
    designDocument.value = normalizeDocument(designDocument.value)
  } catch {
    designDocument.value = createEmptyDocument()
  }

  window.addEventListener('pointermove', handleGlobalPointerMove)
  window.addEventListener('pointerup', finishGesture)
  window.addEventListener('pointercancel', cancelGesture)
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
  window.addEventListener('blur', cancelGesture)
  window.addEventListener('pointerdown', closeMenu)

  emit('ready', api)
  requestAnimationFrame(fitView)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', handleGlobalPointerMove)
  window.removeEventListener('pointerup', finishGesture)
  window.removeEventListener('pointercancel', cancelGesture)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
  window.removeEventListener('blur', cancelGesture)
  window.removeEventListener('pointerdown', closeMenu)

  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <section
    ref="rootRef"
    class="md-model-designer"
    :class="rootClass"
    :style="rootStyle"
    tabindex="0"
  >
    <header v-if="showToolbar" class="md-toolbar">
      <div class="md-toolbar__brand">
        <span class="md-toolbar__logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <rect x="3.5" y="3.5" width="8" height="8" rx="2.3"></rect>
            <rect x="12.5" y="12.5" width="8" height="8" rx="2.3"></rect>
            <path d="M11.5 7.5h3a2 2 0 0 1 2 2v3M12.5 16.5h-3a2 2 0 0 1-2-2v-3"></path>
          </svg>
        </span>
        <span>
          <strong>模型设计器</strong>
          <small>Vue 3.6 Vapor</small>
        </span>
      </div>

      <div class="md-toolbar__divider"></div>

      <div class="md-toolbar__group">
        <button
          class="md-toolbar__button is-primary"
          type="button"
          :disabled="readonly"
          @click="createModelAt()"
        >
          <span>＋</span>
          模型
        </button>

        <button
          class="md-toolbar__button"
          type="button"
          :disabled="readonly"
          @click="createGroupAt()"
        >
          <span>▭</span>
          分组
        </button>

        <button
          class="md-toolbar__button is-accent"
          type="button"
          :disabled="readonly || selectedModelIds.size === 0"
          @click="groupSelected"
        >
          <span>⌘</span>
          所选成组
        </button>
      </div>

      <div class="md-toolbar__divider"></div>

      <div class="md-toolbar__group">
        <button
          class="md-toolbar__button is-icon"
          type="button"
          title="撤销"
          :disabled="!canUndo"
          @click="undo"
        >
          ↶
        </button>
        <button
          class="md-toolbar__button is-icon"
          type="button"
          title="重做"
          :disabled="!canRedo"
          @click="redo"
        >
          ↷
        </button>
        <button
          class="md-toolbar__button is-icon"
          type="button"
          title="适配全部内容"
          @click="fitView"
        >
          ⛶
        </button>
        <button
          class="md-toolbar__button is-icon is-danger"
          type="button"
          title="删除所选"
          :disabled="readonly || selectedCount === 0"
          @click="deleteSelected"
        >
          ⌫
        </button>
      </div>

      <div class="md-toolbar__spacer"></div>

      <span class="md-toolbar__vapor-badge">
        <i></i>
        Vapor
      </span>

      <div class="md-toolbar__group">
        <button
          class="md-toolbar__button"
          type="button"
          :disabled="readonly"
          @click="chooseImportFile"
        >
          ↓ 导入
        </button>
        <button
          class="md-toolbar__button"
          type="button"
          @click="downloadJSON"
        >
          ↑ 导出
        </button>
      </div>
    </header>

    <main class="md-workspace">
      <div
        ref="canvasRef"
        class="md-canvas"
        :class="{
          'is-panning': gesture?.kind === 'pan',
          'is-space-ready': spacePressed && !gesture,
          'is-relation-stage': relationViewActive,
        }"
        :style="canvasStyle"
        @pointerdown="handleCanvasPointerDown"
        @contextmenu.prevent="openCanvasMenu"
        @dblclick="handleCanvasDoubleClick"
        @wheel="handleWheel"
      >
        <div class="md-world" :style="worldStyle">
          <ModelGroupView
            v-for="group in designDocument.groups"
            :key="group.id"
            :group="group"
            :x="groupX(group)"
            :y="groupY(group)"
            :width="groupWidth(group)"
            :height="groupHeight(group)"
            :member-count="designDocument.models.filter((model) => model.groupId === group.id).length"
            :selected="selectedGroupId === group.id"
            :drop-target="dropTargetGroupId === group.id"
            :moving="isGroupMoving(group.id)"
            :resizing="isGroupResizing(group.id)"
            :relation-state="groupRelationState(group.id)"
            @select="selectGroup"
            @movestart="startGroupDrag"
            @resizestart="startGroupResize"
            @contextmenu="openGroupMenu"
            @doubleclick="handleGroupDoubleClick"
          />

          <ModelNodeView
            v-for="model in designDocument.models"
            :key="model.id"
            :model="model"
            :x="modelX(model)"
            :y="modelY(model)"
            :selected="selectedModelIds.has(model.id)"
            :dragging="isModelDragging(model.id)"
            :relation-state="modelRelationState(model.id)"
            :relation-count="modelRelationCount(model.id)"
            @pointerdown="startModelDrag"
            @contextmenu="openModelMenu"
            @menu="openModelMenu"
            @doubleclick="handleModelDoubleClick"
          />
        </div>

        <div v-if="relationFocusModel" class="md-relation-stage">
          <div class="md-relation-stage__backdrop"></div>
          <div class="md-relation-stage__grid"></div>
          <div class="md-relation-stage__scan"></div>

          <div class="md-relation-stage__world" :style="worldStyle">
            <ModelRelations :lines="relationLines" />

            <ModelNodeView
              v-for="model in relationVisibleModels"
              :key="`relation:${model.id}`"
              :model="model"
              :x="relationModelX(model)"
              :y="relationModelY(model)"
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

        <div v-if="isEmpty" class="md-empty-state">
          <span class="md-empty-state__icon" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <rect x="3.5" y="4.5" width="10" height="10" rx="3"></rect>
              <rect x="18.5" y="17.5" width="10" height="10" rx="3"></rect>
              <path d="M13.5 9.5h4a5 5 0 0 1 5 5v3M18.5 22.5h-4a5 5 0 0 1-5-5v-3"></path>
            </svg>
          </span>
          <strong>创建第一个模型</strong>
          <p>右键画板创建模型或分组，也可以双击空白区域快速创建模型。</p>
          <div>
            <button type="button" :disabled="readonly" @click.stop="createModelAt()">
              ＋ 创建模型
            </button>
            <button type="button" :disabled="readonly" @click.stop="createGroupAt()">
              创建分组
            </button>
          </div>
        </div>

        <div class="md-canvas__tips">
          <span><kbd>右键</kbd> 创建</span>
          <span><kbd>Space</kbd> 拖动画板</span>
          <span><kbd>Ctrl</kbd> 多选</span>
        </div>

        <div class="md-zoom-control">
          <button type="button" title="缩小" @click="zoomOut">−</button>
          <button type="button" title="恢复 100%" @click="resetZoom">
            {{ zoomPercentage }}
          </button>
          <button type="button" title="放大" @click="zoomIn">＋</button>
        </div>
      </div>

      <ModelInspector
        v-if="showInspector"
        :models="selectedModels"
        :all-models="designDocument.models"
        :group="selectedGroup"
        :groups="designDocument.groups"
        :group-member-count="selectedGroupMemberCount"
        :readonly="readonly"
        @update-model="patchModel"
        @update-group="patchGroup"
        @add-field="addField"
        @update-field="patchField"
        @delete-field="deleteField"
        @add-event="addModelEvent"
        @update-event="patchModelEvent"
        @delete-event="deleteModelEvent"
        @add-event-parameter="addEventParameter"
        @update-event-parameter="patchEventParameter"
        @delete-event-parameter="deleteEventParameter"
        @add-trigger="addModelTrigger"
        @update-trigger="patchModelTrigger"
        @delete-trigger="deleteModelTrigger"
        @duplicate-models="duplicateModels"
        @delete-models="deleteModels"
        @group-models="groupModels"
        @delete-group="deleteGroup"
        @ungroup="ungroup"
        @fit-group="fitGroup"
        @view-relations="viewRelations"
      />
    </main>

    <footer v-if="showStatusBar" class="md-statusbar">
      <span>模型 {{ designDocument.models.length }}</span>
      <span>分组 {{ designDocument.groups.length }}</span>
      <span>已选 {{ selectedCount }}</span>
      <span v-if="relationFocusModel">关系 {{ focusedRelationEdges.length }}</span>
      <span class="md-statusbar__spacer"></span>
      <span>{{ readonly ? '只读模式' : '编辑模式' }}</span>
      <span>{{ zoomPercentage }}</span>
    </footer>

    <DesignerContextMenu
      :open="menu.open"
      :x="menu.clientX"
      :y="menu.clientY"
      :items="menuItems"
      @select="handleMenuAction"
    />

    <div v-if="toastMessage" class="md-toast">
      {{ toastMessage }}
    </div>
  </section>
</template>
