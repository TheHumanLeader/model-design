<script setup lang="ts" vapor>
import { computed, ref, watch } from 'vue'
import ModelEventsPanel from './ModelEventsPanel.vue'
import ModelFieldsPanel from './ModelFieldsPanel.vue'
import ModelTriggersPanel from './ModelTriggersPanel.vue'
import type {
  EventParameterPatch,
  FieldPatch,
  GroupPatch,
  ModelEventPatch,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelTriggerPatch,
} from '../types'

type ModelTab = 'base' | 'fields' | 'events' | 'triggers'

const props = defineProps<{
  models: ModelNode[]
  allModels: ModelNode[]
  group: ModelGroup | null
  groups: ModelGroup[]
  groupMemberCount: number
  readonly: boolean
}>()

const emit = defineEmits<{
  updateModel: [modelId: string, patch: ModelPatch, mergeKey?: string]
  updateGroup: [groupId: string, patch: GroupPatch, mergeKey?: string]
  addField: [modelId: string]
  updateField: [modelId: string, fieldId: string, patch: FieldPatch, mergeKey?: string]
  deleteField: [modelId: string, fieldId: string]
  addEvent: [modelId: string]
  updateEvent: [modelId: string, eventId: string, patch: ModelEventPatch, mergeKey?: string]
  deleteEvent: [modelId: string, eventId: string]
  addEventParameter: [modelId: string, eventId: string]
  updateEventParameter: [
    modelId: string,
    eventId: string,
    parameterId: string,
    patch: EventParameterPatch,
    mergeKey?: string,
  ]
  deleteEventParameter: [modelId: string, eventId: string, parameterId: string]
  addTrigger: [modelId: string]
  updateTrigger: [
    modelId: string,
    triggerId: string,
    patch: ModelTriggerPatch,
    mergeKey?: string,
  ]
  deleteTrigger: [modelId: string, triggerId: string]
  duplicateModels: [modelIds: string[]]
  deleteModels: [modelIds: string[]]
  groupModels: [modelIds: string[]]
  deleteGroup: [groupId: string]
  ungroup: [groupId: string]
  fitGroup: [groupId: string]
  viewRelations: [modelId: string]
}>()

const tagDraft = ref('')
const activeTab = ref<ModelTab>('fields')
const model = computed(() => (props.models.length === 1 ? props.models[0] ?? null : null))
const isMultiple = computed(() => props.models.length > 1)

const modelPath = computed(() => {
  const current = model.value
  if (!current) return ''

  const group = props.groups.find((candidate) => candidate.id === current.groupId)
  return group ? `根画板 / ${group.name} / ${current.name}` : `根画板 / ${current.name}`
})

watch(
  () => model.value?.id,
  () => {
    tagDraft.value = ''
  },
)

function textValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value
}

function updateModelText(
  current: ModelNode,
  key: 'name' | 'code' | 'purpose',
  event: Event,
): void {
  emit(
    'updateModel',
    current.id,
    { [key]: textValue(event) },
    `model:${current.id}:${key}`,
  )
}

function updateModelGroup(current: ModelNode, event: Event): void {
  emit('updateModel', current.id, {
    groupId: textValue(event) || null,
  })
}

function addModelTags(current: ModelNode): void {
  if (props.readonly) return

  const incoming = tagDraft.value
    .split(/[,，\n]/)
    .map((tag) => tag.trim())
    .filter(Boolean)

  if (incoming.length === 0) return

  const seen = new Set((current.tags ?? []).map((tag) => tag.toLocaleLowerCase()))
  const nextTags = [...(current.tags ?? [])]

  incoming.forEach((tag) => {
    const normalized = tag.slice(0, 32)
    const key = normalized.toLocaleLowerCase()
    if (!normalized || seen.has(key)) return

    seen.add(key)
    nextTags.push(normalized)
  })

  emit('updateModel', current.id, { tags: nextTags.slice(0, 24) })
  tagDraft.value = ''
}

function removeModelTag(current: ModelNode, tag: string): void {
  if (props.readonly) return

  emit('updateModel', current.id, {
    tags: (current.tags ?? []).filter((candidate) => candidate !== tag),
  })
}

function handleTagKeydown(current: ModelNode, event: KeyboardEvent): void {
  if (event.key !== 'Enter' && event.key !== ',' && event.key !== '，') return
  event.preventDefault()
  addModelTags(current)
}

function updateGroupText(
  current: ModelGroup,
  key: 'name' | 'purpose',
  event: Event,
): void {
  emit(
    'updateGroup',
    current.id,
    { [key]: textValue(event) },
    `group:${current.id}:${key}`,
  )
}

function forwardFieldUpdate(
  modelId: string,
  fieldId: string,
  patch: FieldPatch,
  mergeKey?: string,
): void {
  emit('updateField', modelId, fieldId, patch, mergeKey)
}

function forwardFieldDelete(modelId: string, fieldId: string): void {
  emit('deleteField', modelId, fieldId)
}

function forwardEventUpdate(
  modelId: string,
  eventId: string,
  patch: ModelEventPatch,
  mergeKey?: string,
): void {
  emit('updateEvent', modelId, eventId, patch, mergeKey)
}

function forwardEventDelete(modelId: string, eventId: string): void {
  emit('deleteEvent', modelId, eventId)
}

function forwardAddEventParameter(modelId: string, eventId: string): void {
  emit('addEventParameter', modelId, eventId)
}

function forwardParameterUpdate(
  modelId: string,
  eventId: string,
  parameterId: string,
  patch: EventParameterPatch,
  mergeKey?: string,
): void {
  emit('updateEventParameter', modelId, eventId, parameterId, patch, mergeKey)
}

function forwardDeleteEventParameter(
  modelId: string,
  eventId: string,
  parameterId: string,
): void {
  emit('deleteEventParameter', modelId, eventId, parameterId)
}

function forwardTriggerUpdate(
  modelId: string,
  triggerId: string,
  patch: ModelTriggerPatch,
  mergeKey?: string,
): void {
  emit('updateTrigger', modelId, triggerId, patch, mergeKey)
}

function forwardTriggerDelete(modelId: string, triggerId: string): void {
  emit('deleteTrigger', modelId, triggerId)
}
</script>

<template>
  <aside class="md-inspector">
    <header class="md-inspector__header">
      <div>
        <strong>
          {{
            model
              ? model.name || '未命名模型'
              : group
                ? group.name || '未命名分组'
                : isMultiple
                  ? `已选择 ${models.length} 个模型`
                  : '模型设计器'
          }}
        </strong>
        <p>
          {{
            model
              ? model.code || 'unnamed_model'
              : group
                ? `${groupMemberCount} 个模型`
                : isMultiple
                  ? '批量移动、成组或删除'
                  : '选择画板内容后进行配置'
          }}
        </p>
      </div>

      <span v-if="model" class="md-inspector__type">模型</span>
      <span v-else-if="group" class="md-inspector__type">分组</span>
    </header>

    <template v-if="model">
      <nav class="md-inspector-tabs" aria-label="模型配置分类">
        <button
          type="button"
          :class="{ 'is-active': activeTab === 'base' }"
          @click="activeTab = 'base'"
        >
          基础
        </button>
        <button
          type="button"
          :class="{ 'is-active': activeTab === 'fields' }"
          @click="activeTab = 'fields'"
        >
          字段 <i>{{ model.fields.length }}</i>
        </button>
        <button
          type="button"
          :class="{ 'is-active': activeTab === 'events' }"
          @click="activeTab = 'events'"
        >
          事件 <i>{{ model.events.length }}</i>
        </button>
        <button
          type="button"
          :class="{ 'is-active': activeTab === 'triggers' }"
          @click="activeTab = 'triggers'"
        >
          触发器 <i>{{ model.triggers.length }}</i>
        </button>
      </nav>

      <div class="md-inspector__body">
        <section v-if="activeTab === 'base'" class="md-inspector__section is-compact">
          <div class="md-compact-grid">
            <label class="md-compact-field">
              <span>名称</span>
              <input
                :value="model.name"
                :disabled="readonly"
                @input="updateModelText(model, 'name', $event)"
              />
            </label>

            <label class="md-compact-field">
              <span>标识</span>
              <input
                :value="model.code"
                :disabled="readonly"
                spellcheck="false"
                @input="updateModelText(model, 'code', $event)"
              />
            </label>

            <label class="md-compact-field is-wide">
              <span>用途</span>
              <textarea
                :value="model.purpose"
                :disabled="readonly"
                rows="2"
                placeholder="模型职责、边界与使用场景"
                @input="updateModelText(model, 'purpose', $event)"
              ></textarea>
            </label>

            <label class="md-compact-field is-wide">
              <span>所属分组</span>
              <select
                :value="model.groupId || ''"
                :disabled="readonly"
                @change="updateModelGroup(model, $event)"
              >
                <option value="" :selected="!model.groupId">根画板</option>
                <option
                  v-for="candidate in groups"
                  :key="candidate.id"
                  :value="candidate.id"
                  :selected="model.groupId === candidate.id"
                >
                  {{ candidate.name }}
                </option>
              </select>
            </label>
          </div>

          <section class="md-compact-subsection">
            <header>
              <strong>标签</strong>
              <small>{{ model.tags.length }} 个</small>
            </header>

            <div v-if="model.tags.length" class="md-tag-editor__list">
              <span v-for="tag in model.tags" :key="tag" class="md-tag-editor__tag">
                {{ tag }}
                <button
                  type="button"
                  :disabled="readonly"
                  @click="removeModelTag(model, tag)"
                >
                  ×
                </button>
              </span>
            </div>

            <div class="md-tag-editor__control">
              <input
                v-model="tagDraft"
                :disabled="readonly"
                maxlength="128"
                placeholder="输入标签，回车或逗号添加"
                @keydown="handleTagKeydown(model, $event)"
              />
              <button
                type="button"
                :disabled="readonly || !tagDraft.trim()"
                @click="addModelTags(model)"
              >
                添加
              </button>
            </div>
          </section>

          <div class="md-inspector__path" :title="modelPath">
            {{ modelPath }}
          </div>
        </section>

        <ModelFieldsPanel
          v-else-if="activeTab === 'fields'"
          :model="model"
          :all-models="allModels"
          :readonly="readonly"
          @add="emit('addField', $event)"
          @update="forwardFieldUpdate"
          @delete="forwardFieldDelete"
        />

        <ModelEventsPanel
          v-else-if="activeTab === 'events'"
          :model="model"
          :readonly="readonly"
          @add="emit('addEvent', $event)"
          @update="forwardEventUpdate"
          @delete="forwardEventDelete"
          @add-parameter="forwardAddEventParameter"
          @update-parameter="forwardParameterUpdate"
          @delete-parameter="forwardDeleteEventParameter"
        />

        <ModelTriggersPanel
          v-else
          :model="model"
          :readonly="readonly"
          @add="emit('addTrigger', $event)"
          @update="forwardTriggerUpdate"
          @delete="forwardTriggerDelete"
        />
      </div>

      <footer class="md-inspector__quick-actions">
        <button type="button" @click="emit('viewRelations', model.id)">
          关系
        </button>
        <button
          type="button"
          :disabled="readonly"
          @click="emit('duplicateModels', [model.id])"
        >
          复制
        </button>
        <button
          class="is-danger"
          type="button"
          :disabled="readonly"
          @click="emit('deleteModels', [model.id])"
        >
          删除
        </button>
      </footer>
    </template>

    <div v-else class="md-inspector__body">
      <template v-if="group">
        <section class="md-inspector__section is-compact">
          <div class="md-compact-grid">
            <label class="md-compact-field is-wide">
              <span>分组名称</span>
              <input
                :value="group.name"
                :disabled="readonly"
                @input="updateGroupText(group, 'name', $event)"
              />
            </label>

            <label class="md-compact-field is-wide">
              <span>分组用途</span>
              <textarea
                :value="group.purpose"
                :disabled="readonly"
                rows="3"
                @input="updateGroupText(group, 'purpose', $event)"
              ></textarea>
            </label>
          </div>

          <div class="md-inspector__metric-grid">
            <div>
              <span>模型</span>
              <strong>{{ groupMemberCount }}</strong>
            </div>
            <div>
              <span>宽</span>
              <strong>{{ Math.round(group.width) }}</strong>
            </div>
            <div>
              <span>高</span>
              <strong>{{ Math.round(group.height) }}</strong>
            </div>
          </div>

          <div class="md-inspector__actions is-inline">
            <button
              type="button"
              :disabled="readonly"
              @click="emit('fitGroup', group.id)"
            >
              适配内容
            </button>
            <button
              type="button"
              :disabled="readonly"
              @click="emit('ungroup', group.id)"
            >
              解散
            </button>
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('deleteGroup', group.id)"
            >
              删除
            </button>
          </div>
        </section>
      </template>

      <template v-else-if="isMultiple">
        <section class="md-inspector__section is-compact">
          <div class="md-multi-selection is-compact">
            <span>{{ models.length }}</span>
            <strong>个模型已选择</strong>
          </div>

          <div class="md-inspector__actions">
            <button
              type="button"
              :disabled="readonly"
              @click="emit('groupModels', models.map((item) => item.id))"
            >
              组成分组
            </button>
            <button
              type="button"
              :disabled="readonly"
              @click="emit('duplicateModels', models.map((item) => item.id))"
            >
              复制所选
            </button>
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('deleteModels', models.map((item) => item.id))"
            >
              删除所选
            </button>
          </div>
        </section>
      </template>

      <template v-else>
        <section class="md-inspector__empty">
          <span class="md-inspector__empty-icon" aria-hidden="true">⌘</span>
          <strong>选择模型或分组</strong>
          <p>模型配置按基础、字段、事件、触发器分栏，避免长表单堆叠。</p>
        </section>
      </template>
    </div>
  </aside>
</template>
