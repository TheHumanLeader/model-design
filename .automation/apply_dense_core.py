from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/core/document.ts"


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


text = PATH.read_text(encoding="utf-8")

text = replace_once(
    text,
    """  ModelDesignDocument,
  ModelField,
  ModelFieldRelation,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelRelationType,
  Point,
  Rect,
""",
    """  ModelDesignDocument,
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
""",
    "type imports",
)

text = replace_once(
    text,
    "const GROUP_PADDING = 24\nconst GROUP_CONTENT_TOP = GROUP_HEADER_HEIGHT + 18\n",
    "export const GROUP_PADDING = 24\nexport const GROUP_CONTENT_TOP = GROUP_HEADER_HEIGHT + 18\n",
    "group geometry exports",
)

text = replace_between(
    text,
    "type ModelSeed =",
    "export function cloneDocument",
    """type ModelEventSeed = Partial<Omit<ModelEvent, 'parameters'>> & {
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

""",
    "seed types",
)

text = replace_between(
    text,
    "export function createField",
    "export function createGroup",
    """export function createField(seed: Partial<ModelField> = {}): ModelField {
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

""",
    "constructors",
)

text = replace_between(
    text,
    "export function createDemoDocument",
    "export function normalizeDocument",
    """export function createDemoDocument(): ModelDesignDocument {
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

""",
    "demo document",
)

text = replace_between(
    text,
    "export function normalizeDocument",
    "export function normalizeCode",
    """export function normalizeDocument(value: unknown): ModelDesignDocument {
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

""",
    "document normalization",
)

text = replace_once(
    text,
    "export function getDocumentBounds",
    """export function constrainModelMovement(
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

export function getDocumentBounds""",
    "movement constraint",
)

text = replace_between(
    text,
    "export function findFreeModelPosition",
    "export function updateModel",
    """export function findFreeModelPosition(
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

""",
    "free model position",
)

text = replace_between(
    text,
    "function normalizeTags",
    "function finiteNumber",
    """function normalizeTags(value: unknown): string[] {
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

""",
    "normalization helpers",
)

PATH.write_text(text, encoding="utf-8")
print("Core feature applied")
