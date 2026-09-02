<script setup lang="ts" vapor>
import { computed, ref, watch } from 'vue'
import {
  MODEL_TRIGGER_SOURCES,
  MODEL_TRIGGER_SOURCE_LABELS,
  MODEL_TRIGGER_TIMINGS,
  MODEL_TRIGGER_TIMING_LABELS,
} from '../types'
import type {
  ModelNode,
  ModelTrigger,
  ModelTriggerPatch,
  ModelTriggerSource,
  ModelTriggerTiming,
} from '../types'

const props = defineProps<{
  model: ModelNode
  readonly: boolean
}>()

const emit = defineEmits<{
  add: [modelId: string]
  update: [
    modelId: string,
    triggerId: string,
    patch: ModelTriggerPatch,
    mergeKey?: string,
  ]
  delete: [modelId: string, triggerId: string]
}>()

const expandedId = ref<string | null>(null)
const query = ref('')

const filteredTriggers = computed(() => {
  const keyword = query.value.trim().toLocaleLowerCase()
  if (!keyword) return props.model.triggers

  return props.model.triggers.filter((item) =>
    [
      item.name,
      item.condition,
      item.purpose,
      MODEL_TRIGGER_SOURCE_LABELS[item.source],
      eventName(item),
    ].some((value) =>
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

function toggle(triggerId: string): void {
  expandedId.value = expandedId.value === triggerId ? null : triggerId
}

function textValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value
}

function checkedValue(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function updateText(
  item: ModelTrigger,
  key: 'name' | 'condition' | 'purpose',
  event: Event,
): void {
  emit(
    'update',
    props.model.id,
    item.id,
    { [key]: textValue(event) },
    `trigger:${item.id}:${key}`,
  )
}

function updateSource(item: ModelTrigger, event: Event): void {
  const source = textValue(event) as ModelTriggerSource
  const supportsField = source === 'update' || source === 'field-change'

  emit('update', props.model.id, item.id, {
    source,
    fieldId: supportsField ? item.fieldId : null,
  })
}

function updateTiming(item: ModelTrigger, event: Event): void {
  emit('update', props.model.id, item.id, {
    timing: textValue(event) as ModelTriggerTiming,
  })
}

function updateField(item: ModelTrigger, event: Event): void {
  emit('update', props.model.id, item.id, {
    fieldId: textValue(event) || null,
  })
}

function updateEvent(item: ModelTrigger, event: Event): void {
  emit('update', props.model.id, item.id, {
    eventId: textValue(event) || null,
  })
}

function updateEnabled(item: ModelTrigger, event: Event): void {
  emit('update', props.model.id, item.id, {
    enabled: checkedValue(event),
  })
}

function eventName(item: ModelTrigger): string {
  const target = props.model.events.find((event) => event.id === item.eventId)
  return target?.name || target?.code || '未绑定事件'
}

function triggerSummary(item: ModelTrigger): string {
  const source = MODEL_TRIGGER_SOURCE_LABELS[item.source]
  const timing = MODEL_TRIGGER_TIMING_LABELS[item.timing]
  const field =
    item.fieldId
      ? props.model.fields.find((candidate) => candidate.id === item.fieldId)?.name
      : ''

  return `${timing}${source}${field ? ` · ${field}` : ''}`
}
</script>

<template>
  <section class="md-entity-panel">
    <header class="md-entity-panel__tools">
      <label class="md-entity-search">
        <span aria-hidden="true">⌕</span>
        <input v-model="query" placeholder="筛选触发器名称、条件或事件" />
      </label>

      <button
        class="md-compact-add"
        type="button"
        :disabled="readonly"
        @click="emit('add', model.id)"
      >
        ＋ 触发器
      </button>
    </header>

    <div class="md-entity-panel__meta">
      <span>共 {{ model.triggers.length }} 个触发器</span>
      <span v-if="query">{{ filteredTriggers.length }} 个匹配</span>
    </div>

    <div v-if="filteredTriggers.length" class="md-entity-list">
      <article
        v-for="(item, index) in filteredTriggers"
        :key="item.id"
        class="md-entity-item"
        :class="{ 'is-expanded': expandedId === item.id }"
      >
        <button
          class="md-entity-row is-trigger"
          type="button"
          @click="toggle(item.id)"
        >
          <span
            class="md-trigger-state"
            :class="{ 'is-enabled': item.enabled }"
            :title="item.enabled ? '已启用' : '已停用'"
          ></span>

          <span class="md-entity-row__main">
            <strong>{{ item.name || `触发器 ${index + 1}` }}</strong>
            <small>{{ triggerSummary(item) }} → {{ eventName(item) }}</small>
          </span>

          <span class="md-entity-row__badges">
            <i>{{ MODEL_TRIGGER_SOURCE_LABELS[item.source] }}</i>
            <i v-if="!item.enabled">停用</i>
          </span>

          <span class="md-entity-row__expand" aria-hidden="true">
            {{ expandedId === item.id ? '−' : '+' }}
          </span>
        </button>

        <div v-if="expandedId === item.id" class="md-entity-detail">
          <div class="md-compact-grid">
            <label class="md-compact-field">
              <span>名称</span>
              <input
                :value="item.name"
                :disabled="readonly"
                @input="updateText(item, 'name', $event)"
              />
            </label>

            <label class="md-compact-switch">
              <input
                type="checkbox"
                :checked="item.enabled"
                :disabled="readonly"
                @change="updateEnabled(item, $event)"
              />
              <span>启用</span>
            </label>

            <label class="md-compact-field">
              <span>触发来源</span>
              <select
                :value="item.source"
                :disabled="readonly"
                @change="updateSource(item, $event)"
              >
                <option
                  v-for="source in MODEL_TRIGGER_SOURCES"
                  :key="source"
                  :value="source"
                >
                  {{ MODEL_TRIGGER_SOURCE_LABELS[source] }}
                </option>
              </select>
            </label>

            <label class="md-compact-field">
              <span>触发时机</span>
              <select
                :value="item.timing"
                :disabled="readonly"
                @change="updateTiming(item, $event)"
              >
                <option
                  v-for="timing in MODEL_TRIGGER_TIMINGS"
                  :key="timing"
                  :value="timing"
                >
                  {{ MODEL_TRIGGER_TIMING_LABELS[timing] }}
                </option>
              </select>
            </label>

            <label
              v-if="item.source === 'update' || item.source === 'field-change'"
              class="md-compact-field"
            >
              <span>监听字段</span>
              <select
                :value="item.fieldId || ''"
                :disabled="readonly"
                @change="updateField(item, $event)"
              >
                <option value="">任意字段</option>
                <option
                  v-for="field in model.fields"
                  :key="field.id"
                  :value="field.id"
                >
                  {{ field.name }} · {{ field.code }}
                </option>
              </select>
            </label>

            <label class="md-compact-field">
              <span>执行事件</span>
              <select
                :value="item.eventId || ''"
                :disabled="readonly"
                @change="updateEvent(item, $event)"
              >
                <option value="">未绑定</option>
                <option
                  v-for="eventItem in model.events"
                  :key="eventItem.id"
                  :value="eventItem.id"
                >
                  {{ eventItem.name }} · {{ eventItem.code }}
                </option>
              </select>
            </label>

            <label class="md-compact-field is-wide">
              <span>条件</span>
              <input
                :value="item.condition"
                :disabled="readonly"
                spellcheck="false"
                placeholder="例如：status === 'active'；留空表示无条件"
                @input="updateText(item, 'condition', $event)"
              />
            </label>

            <label class="md-compact-field is-wide">
              <span>用途</span>
              <textarea
                :value="item.purpose"
                :disabled="readonly"
                rows="2"
                placeholder="说明该触发器为什么存在"
                @input="updateText(item, 'purpose', $event)"
              ></textarea>
            </label>
          </div>

          <div v-if="model.events.length === 0" class="md-inline-warning">
            当前模型还没有事件 / Function，触发器暂时无法绑定执行目标。
          </div>

          <footer class="md-entity-detail__actions">
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('delete', model.id, item.id)"
            >
              删除触发器
            </button>
          </footer>
        </div>
      </article>
    </div>

    <div v-else class="md-entity-empty">
      {{ query ? '没有匹配触发器' : '尚未定义触发器' }}
    </div>
  </section>
</template>
