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
  'one-to-one': '一对一',
  'one-to-many': '一对多',
  'many-to-one': '多对一',
  'many-to-many': '多对多',
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

function relationTargetField(field: ModelField): ModelField | null {
  const target = relationTarget(field)
  const fieldId = field.relation?.fieldId
  if (!target || !fieldId) return null

  return target.fields.find((candidate) => candidate.id === fieldId) ?? null
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

function updateRelationType(field: ModelField, type: ModelRelationType): void {
  if (!field.relation || field.relation.type === type) return

  emit('update', props.model.id, field.id, {
    relation: {
      ...field.relation,
      type,
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

function sourcePath(field: ModelField): string {
  return `${props.model.code || 'current_model'}.${field.code || 'current_field'}`
}

function targetPath(field: ModelField): string {
  const target = relationTarget(field)
  const targetField = relationTargetField(field)
  return `${target?.code || 'target_model'}.${targetField?.code || '*'}`
}

function relationSentence(field: ModelField): string {
  if (!field.relation) return ''

  const target = relationTarget(field)
  const [sourceCardinality, targetCardinality] =
    MODEL_RELATION_CARDINALITIES[field.relation.type]
  const sourceQuantity = sourceCardinality === '1' ? '1 个' : '多个'
  const targetQuantity = targetCardinality === '1' ? '1 个' : '多个'
  const relationName = field.relation.label.trim() || '关联到'

  return `${sourceQuantity}「${props.model.name || '当前模型'}」${relationName}${targetQuantity}「${target?.name || '目标模型'}」`
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

          <section class="md-compact-subsection md-relation-editor">
            <header>
              <strong>字段关系</strong>
              <small>方向固定：当前字段（引用方）→ 目标字段（被引用方）</small>
            </header>

            <div class="md-relation-targets">
              <label class="md-compact-field is-wide">
                <span>目标模型 / 被引用方</span>
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

              <label v-if="field.relation" class="md-compact-field is-wide">
                <span>目标字段 / 被引用字段</span>
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
                    {{ targetField.name }} · {{ targetField.code }} · {{ targetField.type }}
                  </option>
                </select>
              </label>
            </div>

            <template v-if="field.relation">
              <div class="md-relation-cardinality-picker">
                <span class="md-relation-cardinality-picker__label">
                  <b>数量关系</b>
                  <small>左边永远是当前模型，右边永远是目标模型</small>
                </span>

                <div
                  class="md-relation-cardinality-options"
                  role="radiogroup"
                  aria-label="当前模型到目标模型的数量关系"
                >
                  <button
                    v-for="relationType in MODEL_RELATION_TYPES"
                    :key="relationType"
                    class="md-relation-cardinality-option"
                    :class="{ 'is-active': field.relation.type === relationType }"
                    type="button"
                    role="radio"
                    :aria-checked="field.relation.type === relationType"
                    :aria-label="`${relationTypeLabels[relationType]}：当前 ${MODEL_RELATION_CARDINALITIES[relationType][0]} 到目标 ${MODEL_RELATION_CARDINALITIES[relationType][1]}`"
                    :title="`${relationTypeLabels[relationType]}：当前模型 ${MODEL_RELATION_CARDINALITIES[relationType][0]} → 目标模型 ${MODEL_RELATION_CARDINALITIES[relationType][1]}`"
                    :disabled="readonly"
                    @click="updateRelationType(field, relationType)"
                  >
                    <span class="md-relation-cardinality-option__side">
                      <b>{{ MODEL_RELATION_CARDINALITIES[relationType][0] }}</b>
                      <small>当前</small>
                    </span>
                    <i aria-hidden="true">→</i>
                    <span class="md-relation-cardinality-option__side">
                      <b>{{ MODEL_RELATION_CARDINALITIES[relationType][1] }}</b>
                      <small>目标</small>
                    </span>
                  </button>
                </div>
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

              <div class="md-relation-preview" aria-live="polite">
                <div class="md-relation-endpoint is-source">
                  <span class="md-relation-endpoint__role">当前 / 引用方</span>
                  <strong>{{ model.name || '当前模型' }}</strong>
                  <code>{{ sourcePath(field) }}</code>
                  <b class="md-relation-endpoint__cardinality">
                    {{ MODEL_RELATION_CARDINALITIES[field.relation.type][0] }}
                  </b>
                </div>

                <div class="md-relation-preview__connector">
                  <span>{{ field.relation.label.trim() || '关联到' }}</span>
                  <i aria-hidden="true">▼</i>
                </div>

                <div class="md-relation-endpoint is-target">
                  <span class="md-relation-endpoint__role">目标 / 被引用方</span>
                  <strong>{{ relationTarget(field)?.name || '目标模型' }}</strong>
                  <code>{{ targetPath(field) }}</code>
                  <b class="md-relation-endpoint__cardinality">
                    {{ MODEL_RELATION_CARDINALITIES[field.relation.type][1] }}
                  </b>
                </div>

                <p class="md-relation-preview__sentence">
                  {{ relationSentence(field) }}
                </p>
                <code class="md-relation-preview__path">
                  {{ sourcePath(field) }} → {{ targetPath(field) }}
                </code>
              </div>
            </template>
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
