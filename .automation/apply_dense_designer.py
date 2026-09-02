from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/components/ModelDesigner.vue"


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
    """import {
  DEFAULT_GRID_SIZE,
  GROUP_HEADER_HEIGHT,
  MIN_GROUP_HEIGHT,
  MIN_GROUP_WIDTH,
  MODEL_NODE_BASE_HEIGHT,
  cloneDocument,
  createEmptyDocument,
  createField,
  createGroup,
  createGroupAroundModels,
  createModel,
  ensureGroupContainsMembers,
  findContainingGroup,
  findFreeModelPosition,
  fitGroupToContents,
  getDocumentBounds,
  isSameDocument,
  modelHeight,
  nextName,
  normalizeCode,
  normalizeDocument,
  snap,
} from '../core'
""",
    """import {
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
  nextName,
  normalizeCode,
  normalizeDocument,
  snap,
} from '../core'
""",
    "core imports",
)

text = replace_once(
    text,
    """import type {
  DesignerMenuItem,
  DesignerSelection,
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelDesignerApi,
  ModelField,
  ModelFieldRelation,
  ModelGroup,
  ModelNode,
  ModelPatch,
  Point,
} from '../types'
""",
    """import type {
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
""",
    "type imports",
)

text = replace_once(
    text,
    """  next.models.push(model)
  const finalDocument = groupExists
    ? ensureGroupContainsMembers(next, groupExists)
    : next

  commitDocument(finalDocument, '已创建模型')
""",
    """  next.models.push(model)
  commitDocument(next, '已创建模型')
""",
    "create model without expansion",
)

text = replace_between(
    text,
    "function addField",
    "function patchModel",
    """function addField(modelId: string): void {
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

""",
    "event and trigger handlers",
)

text = replace_between(
    text,
    "function patchModel",
    "function patchGroup",
    """function patchModel(modelId: string, patch: ModelPatch, mergeKey?: string): void {
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

""",
    "model patch",
)

text = replace_between(
    text,
    "function deleteField",
    "function duplicateModels",
    """function deleteField(modelId: string, fieldId: string): void {
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

""",
    "field reference cleanup",
)

text = replace_between(
    text,
    "function duplicateModels",
    "function deleteModels",
    """function duplicateModels(modelIds: string[]): string[] {
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

""",
    "model duplication",
)

text = replace_once(
    text,
    """  dragDeltaX.value = snap(worldDeltaX, props.gridSize)
  dragDeltaY.value = snap(worldDeltaY, props.gridSize)

  if (currentGesture.kind === 'models') {
    updateDropTarget(currentGesture.ids)
  }
""",
    """  const snappedDelta = {
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
""",
    "pointer movement constraint",
)

text = replace_between(
    text,
    "function finishModelDrag",
    "function finishGroupDrag",
    """function finishModelDrag(currentGesture: Extract<Gesture, { kind: 'models' }>): void {
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

""",
    "finish model drag",
)

text = replace_between(
    text,
    "function updateDropTarget",
    "function handleWheel",
    """function updateDropTarget(modelIds: string[]): void {
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

""",
    "drop target detection",
)

text = replace_once(
    text,
    """        @update-model="patchModel"
        @update-group="patchGroup"
        @add-field="addField"
        @update-field="patchField"
        @delete-field="deleteField"
        @duplicate-models="duplicateModels"
        @delete-models="deleteModels"
        @group-models="groupModels"
        @delete-group="deleteGroup"
        @ungroup="ungroup"
        @fit-group="fitGroup"
""",
    """        @update-model="patchModel"
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
""",
    "inspector wiring",
)

PATH.write_text(text, encoding="utf-8")
print("Designer feature applied")
