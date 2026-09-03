<script setup lang="ts" vapor>
import { computed, ref, watch } from 'vue'
import {
  MODEL_FIELD_TYPES,
  MODEL_RELATION_CARDINALITIES,
  MODEL_RELATION_TYPES,
} from '../types'
import type {
  FieldPatch,
  ModelField,
  ModelFieldRelation,
  ModelNode,
  ModelRelationType,
} from '../types'

const props = defineProps<{
  model: ModelNode
  allModels: ModelNode[]
  readonly: boolean
}>()

const emit = defineEmits<{
  add: [modelId: string]
  update: [modelId: string, fieldId: string, patch: FieldPatch, mergeKey?: string]
  delete: [modelId: string, fieldId: string]
}>()

const expandedId = ref<string | null>(null)
const query = ref('')

const relationTypeLabels: Record<ModelRelationType, string> = {
  'one-to-one': '当前 1 → 目标 1',
  'one-to-many': '当前 1 → 目标 N',
  'many-to-one': '当前 N → 目标 1',
  'many-to-many': '当前 N → 目标 N',
}

const filteredFields = computed(() => {
  const keyword = query.value.trim().toLocaleLowerCase()
  if (!keyword) return props.model.fields

  return props.model.fields.filter((field) =>
    [field.name, field.code, field.type, field.purpose].some((value) =>
      String(value || '').toLocaleLowerCase().includes(keyword),
    ),
  )
})

watch(
  () => props.model.id,
  () => {
    expandedId.value = null
    query.value = ''
  },
)

function toggle(fieldId: string): void {
  expandedId.value = expandedId.value === fieldId ? null : fieldId
}

function textValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value
}

function checkedValue(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function updateText(
  field: ModelField,
  key: 'name' | 'code' | 'purpose' | 'type',
  event: Event,
): void {
  emit(
    'update',
    props.model.id,
    field.id,
    { [key]: textValue(event) },
    `field:${field.id}:${key}`,
  )
}

function updateFlag(
  field: ModelField,
  key: 'required' | 'primaryKey' | 'unique',
  event: Event,
): void {
  emit('update', props.model.id, field.id, {
    [key]: checkedValue(event),
  })
}

function relationTarget(field: ModelField): ModelNode | null {
  const modelId = field.relation?.modelId
  return modelId
    ? props.allModels.find((candidate) => candidate.id === modelId) ?? null
    : null
}

function updateRelationModel(field: ModelField, event: Event): void {
  const modelId = textValue(event)

  if (!modelId) {
    emit('update', props.model.id, field.id, { relation: null })
    return
  }

  const target = props.allModels.find((candidate) => candidate.id === modelId)
  if (!target) return

  const previous = field.relation
  const preferredField =
    target.fields.find((candidate) => candidate.primaryKey) ??
    target.fields[0] ??
    null

  const relation: ModelFieldRelation = {
    modelId,
    fieldId:
      previous?.modelId === modelId
        ? previous.fieldId ?? preferredField?.id ?? null
        : preferredField?.id ?? null,
    type: previous?.type ?? 'many-to-one',
    label: previous?.label ?? '',
  }

  emit('update', props.model.id, field.id, { relation })
}

function updateRelationField(field: ModelField, event: Event): void {
  if (!field.relation) return

  emit('update', props.model.id, field.id, {
    relation: {
      ...field.relation,
      fieldId: textValue(event) || null,
    },
  })
}

function updateRelationType(field: ModelField, event: Event): void {
  if (!field.relation) return

  emit('update', props.model.id, field.id, {
    relation: {
      ...field.relation,
      type: textValue(event) as ModelRelationType,
    },
  })
}

function updateRelationLabel(field: ModelField, event: Event): void {
  if (!field.relation) return

  emit(
    'update',
    props.model.id,
    field.id,
    {
      relation: {
        ...field.relation,
        label: textValue(event),
      },
    },
    `field:${field.id}:relation-label`,
  )
}
</script>

<template>
  <section class="md-entity-panel">
    <header class="md-entity-panel__tools">
      <label class="md-entity-search">
        <span aria-hidden="true">⌕</span>
        <input v-model="query" placeholder="筛选字段名称、标识或类型" />
      </label>

      <button
        class="md-compact-add"
        type="button"
        :disabled="readonly"
        @click="emit('add', model.id)"
      >
        ＋ 字段
      </button>
    </header>

    <div class="md-entity-panel__meta">
      <span>共 {{ model.fields.length }} 个字段</span>
      <span v-if="query">{{ filteredFields.length }} 个匹配</span>
    </div>

    <div v-if="filteredFields.length" class="md-entity-list">
      <article
        v-for="(field, index) in filteredFields"
        :key="field.id"
        class="md-entity-item"
        :class="{ 'is-expanded': expandedId === field.id }"
      >
        <button class="md-entity-row" type="button" @click="toggle(field.id)">
          <code class="md-entity-row__type">{{ field.type }}</code>

          <span class="md-entity-row__main">
            <strong>{{ field.name || `字段 ${index + 1}` }}</strong>
            <small>{{ field.code || 'unnamed_field' }}</small>
          </span>

          <span class="md-entity-row__badges">
            <i v-if="field.primaryKey" title="主键">PK</i>
            <i v-if="field.required" title="必填">*</i>
            <i v-if="field.unique" title="唯一">U</i>
            <i v-if="field.relation" class="is-relation" title="存在字段关系">↗</i>
          </span>

          <span class="md-entity-row__expand" aria-hidden="true">
            {{ expandedId === field.id ? '−' : '+' }}
          </span>
        </button>

        <div v-if="expandedId === field.id" class="md-entity-detail">
          <div class="md-compact-grid">
            <label class="md-compact-field">
              <span>名称</span>
              <input
                :value="field.name"
                :disabled="readonly"
                @input="updateText(field, 'name', $event)"
              />
            </label>

            <label class="md-compact-field">
              <span>标识</span>
              <input
                :value="field.code"
                :disabled="readonly"
                spellcheck="false"
                @input="updateText(field, 'code', $event)"
              />
            </label>

            <label class="md-compact-field">
              <span>类型</span>
              <select
                :value="field.type"
                :disabled="readonly"
                @change="updateText(field, 'type', $event)"
              >
                <option
                  v-for="fieldType in MODEL_FIELD_TYPES"
                  :key="fieldType"
                  :value="fieldType"
                  :selected="field.type === fieldType"
                >
                  {{ fieldType }}
                </option>
              </select>
            </label>

            <label class="md-compact-field is-wide">
              <span>用途</span>
              <textarea
                :value="field.purpose"
                :disabled="readonly"
                rows="2"
                placeholder="该字段保存什么，以及在哪里使用"
                @input="updateText(field, 'purpose', $event)"
              ></textarea>
            </label>
          </div>

          <div class="md-inline-flags">
            <label>
              <input
                type="checkbox"
                :checked="field.required"
                :disabled="readonly"
                @change="updateFlag(field, 'required', $event)"
              />
              必填
            </label>
            <label>
              <input
                type="checkbox"
                :checked="field.primaryKey"
                :disabled="readonly"
                @change="updateFlag(field, 'primaryKey', $event)"
              />
              主键
            </label>
            <label>
              <input
                type="checkbox"
                :checked="field.unique"
                :disabled="readonly"
                @change="updateFlag(field, 'unique', $event)"
              />
              唯一
            </label>
          </div>

          <section class="md-compact-subsection">
            <header>
              <strong>关系</strong>
              <small>基数按“当前模型 → 目标模型”读取</small>
            </header>

            <div class="md-compact-grid">
              <label class="md-compact-field is-wide">
                <span>目标模型</span>
                <select
                  :value="field.relation?.modelId || ''"
                  :disabled="readonly"
                  @change="updateRelationModel(field, $event)"
                >
                  <option value="" :selected="!field.relation?.modelId">无关系</option>
                  <option
                    v-for="candidate in allModels"
                    :key="candidate.id"
                    :value="candidate.id"
                    :selected="field.relation?.modelId === candidate.id"
                  >
                    {{ candidate.name }} · {{ candidate.code }}
                  </option>
                </select>
              </label>

              <template v-if="field.relation">
                <label class="md-compact-field">
                  <span>目标字段</span>
                  <select
                    :value="field.relation.fieldId || ''"
                    :disabled="readonly"
                    @change="updateRelationField(field, $event)"
                  >
                    <option value="" :selected="!field.relation.fieldId">仅关联模型</option>
                    <option
                      v-for="targetField in relationTarget(field)?.fields || []"
                      :key="targetField.id"
                      :value="targetField.id"
                      :selected="field.relation.fieldId === targetField.id"
                    >
                      {{ targetField.name }} · {{ targetField.code }}
                    </option>
                  </select>
                </label>

                <label class="md-compact-field">
                  <span>类型</span>
                  <select
                    :value="field.relation.type"
                    :disabled="readonly"
                    @change="updateRelationType(field, $event)"
                  >
                    <option
                      v-for="relationType in MODEL_RELATION_TYPES"
                      :key="relationType"
                      :value="relationType"
                      :selected="field.relation.type === relationType"
                    >
                      {{ relationTypeLabels[relationType] }}
                    </option>
                  </select>
                </label>

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
                  <input
                    :value="field.relation.label"
                    :disabled="readonly"
                    maxlength="80"
                    placeholder="例如：属于、拥有、创建者"
                    @input="updateRelationLabel(field, $event)"
                  />
                </label>
              </template>
            </div>
          </section>

          <footer class="md-entity-detail__actions">
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('delete', model.id, field.id)"
            >
              删除字段
            </button>
          </footer>
        </div>
      </article>
    </div>

    <div v-else class="md-entity-empty">
      {{ query ? '没有匹配字段' : '尚未定义字段' }}
    </div>
  </section>
</template>
