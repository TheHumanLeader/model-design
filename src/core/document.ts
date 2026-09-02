import { createId } from './id'
import type {
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelEvent,
  ModelEventParameter,
  ModelField,
  ModelFieldRelation,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelRelationType,
  ModelTrigger,
  ModelTriggerSource,
  ModelTriggerTiming,
  Point,
  Rect,
} from '../types'

export const MODEL_NODE_WIDTH = 270
export const MODEL_NODE_BASE_HEIGHT = 167
export const GROUP_HEADER_HEIGHT = 48
export const MIN_GROUP_WIDTH = 336
export const MIN_GROUP_HEIGHT = 220
export const DEFAULT_GRID_SIZE = 12

export const GROUP_PADDING = 24
export const GROUP_CONTENT_TOP = GROUP_HEADER_HEIGHT + 18

type ModelEventSeed = Partial<Omit<ModelEvent, 'parameters'>> & {
  parameters?: Array<Partial<ModelEventParameter>>
}

type ModelSeed = Partial<
  Omit<ModelNode, 'id' | 'kind' | 'fields' | 'events' | 'triggers'>
> & {
  id?: string
  fields?: Array<Partial<ModelField>>
  events?: ModelEventSeed[]
  triggers?: Array<Partial<ModelTrigger>>
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
    relation: normalizeFieldRelation(seed.relation),
  }
}

export function createEventParameter(
  seed: Partial<ModelEventParameter> = {},
): ModelEventParameter {
  return {
    id: seed.id || createId('parameter'),
    name: asText(seed.name),
    type: asText(seed.type) || 'unknown',
    purpose: asText(seed.purpose),
    required: Boolean(seed.required),
  }
}

export function createModelEvent(seed: ModelEventSeed = {}): ModelEvent {
  const name = asText(seed.name) || '事件'
  return {
    id: seed.id || createId('event'),
    name,
    code: asText(seed.code) || normalizeCode(name, 'event'),
    purpose: asText(seed.purpose),
    parameters: Array.isArray(seed.parameters)
      ? seed.parameters.map(createEventParameter)
      : [],
    returnType: asText(seed.returnType) || 'void',
    async: Boolean(seed.async),
  }
}

export function createModelTrigger(
  seed: Partial<ModelTrigger> = {},
): ModelTrigger {
  return {
    id: seed.id || createId('trigger'),
    name: asText(seed.name) || '触发器',
    source: normalizeTriggerSource(seed.source),
    timing: normalizeTriggerTiming(seed.timing),
    fieldId: asNullableText(seed.fieldId),
    eventId: asNullableText(seed.eventId),
    condition: asText(seed.condition),
    purpose: asText(seed.purpose),
    enabled: seed.enabled === undefined ? true : Boolean(seed.enabled),
  }
}

export function createModel(seed: ModelSeed = {}): ModelNode {
  const name = asText(seed.name) || '模型'
  const model: ModelNode = {
    id: seed.id || createId('model'),
    kind: 'model',
    name,
    code: asText(seed.code) || normalizeCode(name, 'model'),
    purpose: asText(seed.purpose),
    tags: normalizeTags(seed.tags),
    x: finiteNumber(seed.x, 0),
    y: finiteNumber(seed.y, 0),
    width: Math.max(220, finiteNumber(seed.width, MODEL_NODE_WIDTH)),
    groupId: asNullableText(seed.groupId),
    fields: Array.isArray(seed.fields) ? seed.fields.map(createField) : [],
    events: Array.isArray(seed.events) ? seed.events.map(createModelEvent) : [],
    triggers: Array.isArray(seed.triggers)
      ? seed.triggers.map(createModelTrigger)
      : [],
  }

  cleanInvalidModelReferences(model)
  return model
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
    width: 900,
    height: 470,
  })

  const permission = createModel({
    name: '权限模型',
    code: 'permission',
    purpose: '记录系统中的权限定义',
    tags: ['权限', '安全'],
    x: 610,
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

  const permissionIdField = permission.fields[0]
  const syncPermissionEvent = createModelEvent({
    name: '同步用户权限',
    code: 'syncPermissions',
    purpose: '用户资料变化后重新计算权限快照',
    returnType: 'Promise<void>',
    async: true,
    parameters: [
      {
        name: 'userId',
        type: 'string',
        purpose: '发生变化的用户标识',
        required: true,
      },
    ],
  })

  const user = createModel({
    name: '用户模型',
    code: 'user',
    purpose: '记录用户身份与基础资料',
    tags: ['账户', '身份'],
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
        name: '拥有权限',
        code: 'permission_ids',
        type: 'relation',
        purpose: '用户拥有的权限集合',
        relation: {
          modelId: permission.id,
          fieldId: permissionIdField?.id ?? null,
          type: 'many-to-many',
          label: '拥有权限',
        },
      },
    ],
    events: [syncPermissionEvent],
    triggers: [
      {
        name: '用户更新后同步权限',
        source: 'update',
        timing: 'after',
        eventId: syncPermissionEvent.id,
        condition: '',
        purpose: '确保用户资料与权限快照保持一致',
        enabled: true,
      },
    ],
  })

  const auditLog = createModel({
    name: '审计日志',
    code: 'audit_log',
    purpose: '记录独立的系统操作日志，用于演示无关模型透明化',
    tags: ['审计', '日志'],
    x: 850,
    y: 184,
    fields: [
      {
        name: '日志标识',
        code: 'log_id',
        type: 'id',
        required: true,
        primaryKey: true,
        unique: true,
      },
      {
        name: '操作内容',
        code: 'content',
        type: 'text',
        purpose: '记录操作摘要',
        required: true,
      },
    ],
  })

  return {
    version: 1,
    groups: [group],
    models: [user, permission, auditLog],
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
      const rawFields = Array.isArray(model.fields)
        ? model.fields.filter(isRecord)
        : []
      const rawEvents = Array.isArray(model.events)
        ? model.events.filter(isRecord)
        : []
      const rawTriggers = Array.isArray(model.triggers)
        ? model.triggers.filter(isRecord)
        : []
      const groupId = asNullableText(model.groupId)

      return createModel({
        id: asText(model.id) || undefined,
        name: asText(model.name) || undefined,
        code: asText(model.code),
        purpose: asText(model.purpose),
        tags: normalizeTags(model.tags),
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
          relation: normalizeFieldRelation(field.relation),
        })),
        events: rawEvents.map((item) => {
          const rawParameters = Array.isArray(item.parameters)
            ? item.parameters.filter(isRecord)
            : []

          return {
            id: asText(item.id) || undefined,
            name: asText(item.name),
            code: asText(item.code),
            purpose: asText(item.purpose),
            returnType: asText(item.returnType) || 'void',
            async: Boolean(item.async),
            parameters: rawParameters.map((parameter) => ({
              id: asText(parameter.id) || undefined,
              name: asText(parameter.name),
              type: asText(parameter.type) || 'unknown',
              purpose: asText(parameter.purpose),
              required: Boolean(parameter.required),
            })),
          }
        }),
        triggers: rawTriggers.map((trigger) => ({
          id: asText(trigger.id) || undefined,
          name: asText(trigger.name),
          source: normalizeTriggerSource(trigger.source),
          timing: normalizeTriggerTiming(trigger.timing),
          fieldId: asNullableText(trigger.fieldId),
          eventId: asNullableText(trigger.eventId),
          condition: asText(trigger.condition),
          purpose: asText(trigger.purpose),
          enabled:
            trigger.enabled === undefined
              ? true
              : Boolean(trigger.enabled),
        })),
      })
    })

  const normalizedModels = deduplicateIds(models, 'model')
  normalizedModels.forEach(cleanInvalidModelReferences)
  cleanInvalidRelations(normalizedModels)

  return {
    version: 1,
    models: normalizedModels,
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
  const tagHeight = (model.tags?.length ?? 0) > 0 ? 34 : 0
  const fieldAreaHeight =
    visibleFieldCount === 0
      ? 41
      : 12 +
        visibleFieldCount * 31 +
        (model.fields.length > 4 ? 34 : 0)

  return 58 + 43 + tagHeight + fieldAreaHeight + 25
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

export function constrainModelMovement(
  document: ModelDesignDocument,
  modelIds: Iterable<string>,
  delta: Point,
): Point {
  const selectedIds = new Set(modelIds)
  let minimumX = Number.NEGATIVE_INFINITY
  let maximumX = Number.POSITIVE_INFINITY
  let minimumY = Number.NEGATIVE_INFINITY
  let maximumY = Number.POSITIVE_INFINITY

  document.models.forEach((model) => {
    if (!selectedIds.has(model.id) || !model.groupId) return

    const group = document.groups.find(
      (candidate) => candidate.id === model.groupId,
    )
    if (!group) return

    const contentLeft = group.x + GROUP_PADDING
    const contentTop = group.y + GROUP_CONTENT_TOP
    const contentRight = group.x + group.width - GROUP_PADDING
    const contentBottom = group.y + group.height - GROUP_PADDING

    minimumX = Math.max(minimumX, contentLeft - model.x)
    maximumX = Math.min(maximumX, contentRight - model.width - model.x)
    minimumY = Math.max(minimumY, contentTop - model.y)
    maximumY = Math.min(
      maximumY,
      contentBottom - modelHeight(model) - model.y,
    )
  })

  return {
    x:
      minimumX === Number.NEGATIVE_INFINITY
        ? delta.x
        : clamp(delta.x, minimumX, Math.max(minimumX, maximumX)),
    y:
      minimumY === Number.NEGATIVE_INFINITY
        ? delta.y
        : clamp(delta.y, minimumY, Math.max(minimumY, maximumY)),
  }
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
    const minY = group.y + GROUP_CONTENT_TOP
    const maxX = Math.max(
      minX,
      group.x + group.width - MODEL_NODE_WIDTH - GROUP_PADDING,
    )
    const maxY = Math.max(
      minY,
      group.y + group.height - MODEL_NODE_BASE_HEIGHT - GROUP_PADDING,
    )
    const inside = {
      x: snap(clamp(origin.x, minX, maxX), gridSize),
      y: snap(clamp(origin.y, minY, maxY), gridSize),
    }

    if (isModelPositionFree(document, inside, ignoredModelId)) {
      return inside
    }

    const gap = 18
    const usableWidth = Math.max(MODEL_NODE_WIDTH, group.width - GROUP_PADDING * 2)
    const columns = Math.max(
      1,
      Math.floor((usableWidth + gap) / (MODEL_NODE_WIDTH + gap)),
    )

    for (let index = 0; index < 160; index += 1) {
      const column = index % columns
      const row = Math.floor(index / columns)
      const candidate = {
        x: snap(minX + column * (MODEL_NODE_WIDTH + gap), gridSize),
        y: snap(minY + row * (MODEL_NODE_BASE_HEIGHT + gap), gridSize),
      }

      if (candidate.x > maxX || candidate.y > maxY) {
        continue
      }

      if (isModelPositionFree(document, candidate, ignoredModelId)) {
        return candidate
      }
    }

    return inside
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
  if (patch.tags !== undefined) model.tags = normalizeTags(patch.tags)
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

function normalizeTags(value: unknown): string[] {
  const source = Array.isArray(value)
    ? value
    : typeof value === 'string'
      ? value.split(/[,，]/)
      : []
  const seen = new Set<string>()
  const tags: string[] = []

  source.forEach((item) => {
    const tag = asText(item).trim().slice(0, 32)
    const key = tag.toLocaleLowerCase()
    if (!tag || seen.has(key)) return

    seen.add(key)
    tags.push(tag)
  })

  return tags.slice(0, 24)
}

function normalizeFieldRelation(value: unknown): ModelFieldRelation | null {
  if (!isRecord(value)) return null

  const modelId = asText(value.modelId).trim()
  if (!modelId) return null

  return {
    modelId,
    fieldId: asNullableText(value.fieldId),
    type: normalizeRelationType(value.type),
    label: asText(value.label).trim().slice(0, 80),
  }
}

function normalizeRelationType(value: unknown): ModelRelationType {
  switch (value) {
    case 'one-to-one':
    case 'one-to-many':
    case 'many-to-one':
    case 'many-to-many':
      return value
    default:
      return 'many-to-one'
  }
}

function normalizeTriggerSource(value: unknown): ModelTriggerSource {
  switch (value) {
    case 'create':
    case 'update':
    case 'delete':
    case 'field-change':
    case 'custom':
      return value
    default:
      return 'update'
  }
}

function normalizeTriggerTiming(value: unknown): ModelTriggerTiming {
  return value === 'before' ? 'before' : 'after'
}

function cleanInvalidModelReferences(model: ModelNode): void {
  const fieldIds = new Set(model.fields.map((field) => field.id))
  const eventIds = new Set(model.events.map((item) => item.id))

  model.triggers.forEach((trigger) => {
    if (trigger.fieldId && !fieldIds.has(trigger.fieldId)) {
      trigger.fieldId = null
    }

    if (trigger.eventId && !eventIds.has(trigger.eventId)) {
      trigger.eventId = null
    }

    if (trigger.source !== 'update' && trigger.source !== 'field-change') {
      trigger.fieldId = null
    }
  })
}

function cleanInvalidRelations(models: ModelNode[]): void {
  const modelsById = new Map(models.map((model) => [model.id, model]))

  models.forEach((model) => {
    model.fields.forEach((field) => {
      const relation = field.relation
      if (!relation) return

      const target = modelsById.get(relation.modelId)
      if (!target) {
        field.relation = null
        return
      }

      if (
        relation.fieldId &&
        !target.fields.some((candidate) => candidate.id === relation.fieldId)
      ) {
        relation.fieldId = null
      }
    })
  })
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
