from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src/components/ModelDesigner.vue"
text = path.read_text(encoding="utf-8")

if "function patchModelEvent(" in text:
    print("dense designer handlers already exist")
    raise SystemExit(0)

marker = "function patchModel(modelId: string, patch: ModelPatch, mergeKey?: string): void {"
if text.count(marker) != 1:
    raise RuntimeError(f"expected one patchModel marker, found {text.count(marker)}")

handlers = r'''function patchModelEvent(
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

'''

text = text.replace(marker, handlers + marker, 1)
path.write_text(text, encoding="utf-8")
print("dense designer handlers restored")
