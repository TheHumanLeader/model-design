import { createId } from './id'
import type {
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelField,
  ModelGroup,
  ModelNode,
  ModelPatch,
  Point,
  Rect,
} from '../types'

export const MODEL_NODE_WIDTH = 270
export const MODEL_NODE_BASE_HEIGHT = 144
export const GROUP_HEADER_HEIGHT = 48
export const MIN_GROUP_WIDTH = 336
export const MIN_GROUP_HEIGHT = 220
export const DEFAULT_GRID_SIZE = 12

const GROUP_PADDING = 24
const GROUP_CONTENT_TOP = GROUP_HEADER_HEIGHT + 18

type ModelSeed = Partial<Omit<ModelNode, 'id' | 'kind' | 'fields'>> & {
  id?: string
  fields?: Array<Partial<ModelField>>
}

type GroupSeed = Partial<Omit<ModelGroup, 'id' | 'kind'>> & {
  id?: string
}

export function cloneDocument(document: ModelDesignDocument): ModelDesignDocument {
  if (typeof structuredClone === 'function') {
    return structuredClone(document)
  }

  return JSON.parse(JSON.stringify(document)) as ModelDesignDocument
}

export function createEmptyDocument(): ModelDesignDocument {
  return {
    version: 1,
    models: [],
    groups: [],
  }
}

export function createField(seed: Partial<ModelField> = {}): ModelField {
  const name = asText(seed.name)
  return {
    id: seed.id || createId('field'),
    name,
    code: asText(seed.code) || normalizeCode(name, 'field'),
    type: asText(seed.type) || 'string',
    purpose: asText(seed.purpose),
    required: Boolean(seed.required),
    primaryKey: Boolean(seed.primaryKey),
    unique: Boolean(seed.unique),
  }
}

export function createModel(seed: ModelSeed = {}): ModelNode {
  const name = asText(seed.name) || '模型'
  return {
    id: seed.id || createId('model'),
    kind: 'model',
    name,
    code: asText(seed.code) || normalizeCode(name, 'model'),
    purpose: asText(seed.purpose),
    x: finiteNumber(seed.x, 0),
    y: finiteNumber(seed.y, 0),
    width: Math.max(220, finiteNumber(seed.width, MODEL_NODE_WIDTH)),
    groupId: asNullableText(seed.groupId),
    fields: Array.isArray(seed.fields) ? seed.fields.map(createField) : [],
  }
}

export function createGroup(seed: GroupSeed = {}): ModelGroup {
  return {
    id: seed.id || createId('group'),
    kind: 'group',
    name: asText(seed.name) || '分组',
    purpose: asText(seed.purpose),
    x: finiteNumber(seed.x, 0),
    y: finiteNumber(seed.y, 0),
    width: Math.max(MIN_GROUP_WIDTH, finiteNumber(seed.width, 430)),
    height: Math.max(MIN_GROUP_HEIGHT, finiteNumber(seed.height, 300)),
  }
}

export function createDemoDocument(): ModelDesignDocument {
  const group = createGroup({
    name: '用户与权限',
    purpose: '账号、角色与权限领域模型',
    x: 96,
    y: 84,
    width: 680,
    height: 470,
  })

  const user = createModel({
    name: '用户模型',
    code: 'user',
    purpose: '记录用户身份与基础资料',
    x: 130,
    y: 164,
    groupId: group.id,
    fields: [
      {
        name: '用户标识',
        code: 'user_id',
        type: 'id',
        purpose: '用户唯一标识',
        required: true,
        primaryKey: true,
        unique: true,
      },
      {
        name: '用户名',
        code: 'username',
        type: 'string',
        purpose: '用户登录名',
        required: true,
        unique: true,
      },
      {
        name: '显示名称',
        code: 'display_name',
        type: 'string',
        purpose: '界面展示名称',
      },
    ],
  })

  const permission = createModel({
    name: '权限模型',
    code: 'permission',
    purpose: '记录系统中的权限定义',
    x: 430,
    y: 164,
    groupId: group.id,
    fields: [
      {
        name: '权限标识',
        code: 'permission_id',
        type: 'id',
        purpose: '权限唯一标识',
        required: true,
        primaryKey: true,
        unique: true,
      },
      {
        name: '权限编码',
        code: 'permission_code',
        type: 'string',
        purpose: '程序使用的权限编码',
        required: true,
        unique: true,
      },
    ],
  })

  return {
    version: 1,
    groups: [group],
    models: [user, permission],
  }
}

export function normalizeDocument(value: unknown): ModelDesignDocument {
  if (!isRecord(value)) {
    throw new TypeError('导入内容不是有效的模型设计文档')
  }

  const rawGroups = Array.isArray(value.groups) ? value.groups : []
  const groups = rawGroups
    .filter(isRecord)
    .map((group) =>
      createGroup({
        id: asText(group.id) || undefined,
        name: asText(group.name) || undefined,
        purpose: asText(group.purpose),
        x: finiteNumber(group.x, 0),
        y: finiteNumber(group.y, 0),
        width: finiteNumber(group.width, 430),
        height: finiteNumber(group.height, 300),
      }),
    )

  const groupIds = new Set(groups.map((group) => group.id))
  const rawModels = Array.isArray(value.models) ? value.models : []
  const models = rawModels
    .filter(isRecord)
    .map((model) => {
      const rawFields = Array.isArray(model.fields) ? model.fields.filter(isRecord) : []
      const groupId = asNullableText(model.groupId)

      return createModel({
        id: asText(model.id) || undefined,
        name: asText(model.name) || undefined,
        code: asText(model.code),
        purpose: asText(model.purpose),
        x: finiteNumber(model.x, 0),
        y: finiteNumber(model.y, 0),
        width: finiteNumber(model.width, MODEL_NODE_WIDTH),
        groupId: groupId && groupIds.has(groupId) ? groupId : null,
        fields: rawFields.map((field) => ({
          id: asText(field.id) || undefined,
          name: asText(field.name),
          code: asText(field.code),
          type: asText(field.type) || 'string',
          purpose: asText(field.purpose),
          required: Boolean(field.required),
          primaryKey: Boolean(field.primaryKey ?? field.primary),
          unique: Boolean(field.unique),
        })),
      })
    })

  return {
    version: 1,
    models: deduplicateIds(models, 'model'),
    groups: deduplicateIds(groups, 'group'),
  }
}

export function normalizeCode(value: string, fallback = 'model'): string {
  const normalized = value
    .trim()
    .replace(/[\s-]+/g, '_')
    .replace(/[^\p{L}\p{N}_]/gu, '')
    .replace(/^(\d)/, '_$1')
    .toLowerCase()

  return normalized || fallback
}

export function nextName(base: string, names: Iterable<string>): string {
  const used = new Set(names)

  if (!used.has(base)) {
    return base
  }

  let index = 2
  while (used.has(`${base} ${index}`)) {
    index += 1
  }

  return `${base} ${index}`
}

export function snap(value: number, gridSize = DEFAULT_GRID_SIZE): number {
  if (gridSize <= 0) {
    return value
  }

  return Math.round(value / gridSize) * gridSize
}

export function modelHeight(model: ModelNode): number {
  const visibleFieldCount = Math.min(model.fields.length, 4)

  if (visibleFieldCount === 0) {
    return MODEL_NODE_BASE_HEIGHT
  }

  return MODEL_NODE_BASE_HEIGHT + visibleFieldCount * 31 + (model.fields.length > 4 ? 26 : 0)
}

export function modelRect(model: ModelNode): Rect {
  return {
    x: model.x,
    y: model.y,
    width: model.width,
    height: modelHeight(model),
  }
}

export function containsPoint(rect: Rect, point: Point): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  )
}

export function findContainingGroup(
  document: ModelDesignDocument,
  point: Point,
  excludedGroupId: string | null = null,
): ModelGroup | null {
  return (
    document.groups
      .filter((group) => group.id !== excludedGroupId && containsPoint(group, point))
      .sort((left, right) => left.width * left.height - right.width * right.height)[0] ?? null
  )
}

export function getDocumentBounds(document: ModelDesignDocument): Rect | null {
  const rectangles: Rect[] = [
    ...document.groups,
    ...document.models.map(modelRect),
  ]

  if (rectangles.length === 0) {
    return null
  }

  const minX = Math.min(...rectangles.map((rect) => rect.x))
  const minY = Math.min(...rectangles.map((rect) => rect.y))
  const maxX = Math.max(...rectangles.map((rect) => rect.x + rect.width))
  const maxY = Math.max(...rectangles.map((rect) => rect.y + rect.height))

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  }
}

export function findFreeModelPosition(
  document: ModelDesignDocument,
  position: Point,
  groupId: string | null,
  gridSize = DEFAULT_GRID_SIZE,
  ignoredModelId: string | null = null,
): Point {
  const group = groupId
    ? document.groups.find((candidate) => candidate.id === groupId) ?? null
    : null

  const origin = {
    x: snap(position.x, gridSize),
    y: snap(position.y, gridSize),
  }

  if (group) {
    const minX = group.x + GROUP_PADDING
    const maxX = Math.max(minX, group.x + group.width - MODEL_NODE_WIDTH - GROUP_PADDING)
    const minY = group.y + GROUP_CONTENT_TOP
    const inside = {
      x: snap(clamp(origin.x, minX, maxX), gridSize),
      y: snap(Math.max(origin.y, minY), gridSize),
    }

    if (isModelPositionFree(document, inside, ignoredModelId)) {
      return inside
    }

    const gap = 24
    const usableWidth = Math.max(MODEL_NODE_WIDTH, group.width - GROUP_PADDING * 2)
    const columns = Math.max(1, Math.floor((usableWidth + gap) / (MODEL_NODE_WIDTH + gap)))

    for (let index = 0; index < 160; index += 1) {
      const column = index % columns
      const row = Math.floor(index / columns)
      const candidate = {
        x: snap(minX + column * (MODEL_NODE_WIDTH + gap), gridSize),
        y: snap(minY + row * (MODEL_NODE_BASE_HEIGHT + gap), gridSize),
      }

      if (isModelPositionFree(document, candidate, ignoredModelId)) {
        return candidate
      }
    }
  }

  if (isModelPositionFree(document, origin, ignoredModelId)) {
    return origin
  }

  const stepX = MODEL_NODE_WIDTH + 36
  const stepY = MODEL_NODE_BASE_HEIGHT + 44

  for (let radius = 1; radius <= 18; radius += 1) {
    for (let row = -radius; row <= radius; row += 1) {
      for (let column = -radius; column <= radius; column += 1) {
        if (Math.max(Math.abs(row), Math.abs(column)) !== radius) {
          continue
        }

        const candidate = {
          x: snap(origin.x + column * stepX, gridSize),
          y: snap(origin.y + row * stepY, gridSize),
        }

        if (isModelPositionFree(document, candidate, ignoredModelId)) {
          return candidate
        }
      }
    }
  }

  return {
    x: origin.x + document.models.length * 24,
    y: origin.y + document.models.length * 24,
  }
}

export function updateModel(
  document: ModelDesignDocument,
  modelId: string,
  patch: ModelPatch,
): ModelDesignDocument {
  const next = cloneDocument(document)
  const model = next.models.find((candidate) => candidate.id === modelId)

  if (!model) {
    return next
  }

  if (patch.name !== undefined) model.name = patch.name
  if (patch.code !== undefined) model.code = patch.code
  if (patch.purpose !== undefined) model.purpose = patch.purpose
  if (patch.groupId !== undefined) {
    model.groupId =
      patch.groupId && next.groups.some((group) => group.id === patch.groupId)
        ? patch.groupId
        : null
  }

  return next
}

export function updateGroup(
  document: ModelDesignDocument,
  groupId: string,
  patch: GroupPatch,
): ModelDesignDocument {
  const next = cloneDocument(document)
  const group = next.groups.find((candidate) => candidate.id === groupId)

  if (!group) {
    return next
  }

  if (patch.name !== undefined) group.name = patch.name
  if (patch.purpose !== undefined) group.purpose = patch.purpose

  return next
}

export function updateField(
  document: ModelDesignDocument,
  modelId: string,
  fieldId: string,
  patch: FieldPatch,
): ModelDesignDocument {
  const next = cloneDocument(document)
  const field = next.models
    .find((model) => model.id === modelId)
    ?.fields.find((candidate) => candidate.id === fieldId)

  if (!field) {
    return next
  }

  Object.assign(field, patch)
  return next
}

export function createGroupAroundModels(
  document: ModelDesignDocument,
  modelIds: Iterable<string>,
  name?: string,
): { document: ModelDesignDocument; group: ModelGroup | null } {
  const idSet = new Set(modelIds)
  const selected = document.models.filter((model) => idSet.has(model.id))

  if (selected.length === 0) {
    return {
      document: cloneDocument(document),
      group: null,
    }
  }

  const minX = Math.min(...selected.map((model) => model.x))
  const minY = Math.min(...selected.map((model) => model.y))
  const maxX = Math.max(...selected.map((model) => model.x + model.width))
  const maxY = Math.max(...selected.map((model) => model.y + modelHeight(model)))

  const group = createGroup({
    name: name || nextName('分组', document.groups.map((item) => item.name)),
    x: minX - GROUP_PADDING,
    y: minY - GROUP_CONTENT_TOP,
    width: Math.max(MIN_GROUP_WIDTH, maxX - minX + GROUP_PADDING * 2),
    height: Math.max(MIN_GROUP_HEIGHT, maxY - minY + GROUP_CONTENT_TOP + GROUP_PADDING),
  })

  const next = cloneDocument(document)
  next.groups.push(group)
  next.models.forEach((model) => {
    if (idSet.has(model.id)) {
      model.groupId = group.id
    }
  })

  return { document: next, group }
}

export function fitGroupToContents(
  document: ModelDesignDocument,
  groupId: string,
): ModelDesignDocument {
  const next = cloneDocument(document)
  const group = next.groups.find((candidate) => candidate.id === groupId)

  if (!group) {
    return next
  }

  const models = next.models.filter((model) => model.groupId === groupId)

  if (models.length === 0) {
    group.width = Math.max(group.width, MIN_GROUP_WIDTH)
    group.height = Math.max(group.height, MIN_GROUP_HEIGHT)
    return next
  }

  const minX = Math.min(...models.map((model) => model.x))
  const minY = Math.min(...models.map((model) => model.y))
  const maxX = Math.max(...models.map((model) => model.x + model.width))
  const maxY = Math.max(...models.map((model) => model.y + modelHeight(model)))

  group.x = minX - GROUP_PADDING
  group.y = minY - GROUP_CONTENT_TOP
  group.width = Math.max(MIN_GROUP_WIDTH, maxX - minX + GROUP_PADDING * 2)
  group.height = Math.max(MIN_GROUP_HEIGHT, maxY - minY + GROUP_CONTENT_TOP + GROUP_PADDING)

  return next
}

export function ensureGroupContainsMembers(
  document: ModelDesignDocument,
  groupId: string,
): ModelDesignDocument {
  const next = cloneDocument(document)
  const group = next.groups.find((candidate) => candidate.id === groupId)

  if (!group) {
    return next
  }

  const members = next.models.filter((model) => model.groupId === groupId)
  if (members.length === 0) {
    return next
  }

  const minX = Math.min(...members.map((model) => model.x - GROUP_PADDING))
  const minY = Math.min(...members.map((model) => model.y - GROUP_CONTENT_TOP))
  const maxX = Math.max(...members.map((model) => model.x + model.width + GROUP_PADDING))
  const maxY = Math.max(...members.map((model) => model.y + modelHeight(model) + GROUP_PADDING))

  const currentRight = group.x + group.width
  const currentBottom = group.y + group.height

  const nextX = Math.min(group.x, minX)
  const nextY = Math.min(group.y, minY)
  const nextRight = Math.max(currentRight, maxX)
  const nextBottom = Math.max(currentBottom, maxY)

  group.x = nextX
  group.y = nextY
  group.width = Math.max(MIN_GROUP_WIDTH, nextRight - nextX)
  group.height = Math.max(MIN_GROUP_HEIGHT, nextBottom - nextY)

  return next
}

export function isSameDocument(
  left: ModelDesignDocument,
  right: ModelDesignDocument,
): boolean {
  return JSON.stringify(left) === JSON.stringify(right)
}

function isModelPositionFree(
  document: ModelDesignDocument,
  position: Point,
  ignoredModelId: string | null,
): boolean {
  const margin = 16

  return !document.models.some((model) => {
    if (model.id === ignoredModelId) {
      return false
    }

    return (
      position.x < model.x + model.width + margin &&
      position.x + MODEL_NODE_WIDTH + margin > model.x &&
      position.y < model.y + modelHeight(model) + margin &&
      position.y + MODEL_NODE_BASE_HEIGHT + margin > model.y
    )
  })
}

function deduplicateIds<T extends { id: string }>(items: T[], prefix: string): T[] {
  const used = new Set<string>()

  return items.map((item) => {
    if (!used.has(item.id)) {
      used.add(item.id)
      return item
    }

    const id = createId(prefix)
    used.add(id)
    return {
      ...item,
      id,
    }
  })
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function asNullableText(value: unknown): string | null {
  const text = asText(value).trim()
  return text || null
}

function finiteNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
