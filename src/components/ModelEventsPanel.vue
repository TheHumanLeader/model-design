<script setup lang="ts" vapor>
import { computed, ref, watch } from 'vue'
import type {
  EventParameterPatch,
  ModelEvent,
  ModelEventParameter,
  ModelEventPatch,
  ModelNode,
} from '../types'

const props = defineProps<{
  model: ModelNode
  readonly: boolean
}>()

const emit = defineEmits<{
  add: [modelId: string]
  update: [modelId: string, eventId: string, patch: ModelEventPatch, mergeKey?: string]
  delete: [modelId: string, eventId: string]
  addParameter: [modelId: string, eventId: string]
  updateParameter: [
    modelId: string,
    eventId: string,
    parameterId: string,
    patch: EventParameterPatch,
    mergeKey?: string,
  ]
  deleteParameter: [modelId: string, eventId: string, parameterId: string]
}>()

const expandedId = ref<string | null>(null)
const query = ref('')

const filteredEvents = computed(() => {
  const keyword = query.value.trim().toLocaleLowerCase()
  if (!keyword) return props.model.events

  return props.model.events.filter((item) =>
    [item.name, item.code, item.purpose, item.returnType].some((value) =>
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

function toggle(eventId: string): void {
  expandedId.value = expandedId.value === eventId ? null : eventId
}

function textValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value
}

function checkedValue(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function updateText(
  item: ModelEvent,
  key: 'name' | 'code' | 'purpose' | 'returnType',
  event: Event,
): void {
  emit(
    'update',
    props.model.id,
    item.id,
    { [key]: textValue(event) },
    `event:${item.id}:${key}`,
  )
}

function updateAsync(item: ModelEvent, event: Event): void {
  emit('update', props.model.id, item.id, {
    async: checkedValue(event),
  })
}

function updateParameterText(
  item: ModelEvent,
  parameter: ModelEventParameter,
  key: 'name' | 'type' | 'purpose',
  event: Event,
): void {
  emit(
    'updateParameter',
    props.model.id,
    item.id,
    parameter.id,
    { [key]: textValue(event) },
    `event-parameter:${parameter.id}:${key}`,
  )
}

function updateParameterRequired(
  item: ModelEvent,
  parameter: ModelEventParameter,
  event: Event,
): void {
  emit('updateParameter', props.model.id, item.id, parameter.id, {
    required: checkedValue(event),
  })
}

function signature(item: ModelEvent): string {
  const parameters = item.parameters
    .slice(0, 3)
    .map((parameter) => `${parameter.name || 'arg'}: ${parameter.type || 'unknown'}`)
    .join(', ')
  const hidden = item.parameters.length > 3 ? ', …' : ''

  return `${item.code || 'unnamed'}(${parameters}${hidden})`
}
</script>

<template>
  <section class="md-entity-panel">
    <header class="md-entity-panel__tools">
      <label class="md-entity-search">
        <span aria-hidden="true">⌕</span>
        <input v-model="query" placeholder="筛选事件名称或函数标识" />
      </label>

      <button
        class="md-compact-add"
        type="button"
        :disabled="readonly"
        @click="emit('add', model.id)"
      >
        ＋ 事件
      </button>
    </header>

    <div class="md-entity-panel__meta">
      <span>共 {{ model.events.length }} 个事件 / Function</span>
      <span v-if="query">{{ filteredEvents.length }} 个匹配</span>
    </div>

    <div v-if="filteredEvents.length" class="md-entity-list">
      <article
        v-for="(item, index) in filteredEvents"
        :key="item.id"
        class="md-entity-item"
        :class="{ 'is-expanded': expandedId === item.id }"
      >
        <button class="md-entity-row" type="button" @click="toggle(item.id)">
          <code class="md-entity-row__type is-function">fn</code>

          <span class="md-entity-row__main">
            <strong>{{ item.name || `事件 ${index + 1}` }}</strong>
            <small>{{ signature(item) }}</small>
          </span>

          <span class="md-entity-row__badges">
            <i v-if="item.async">async</i>
            <i>{{ item.returnType || 'void' }}</i>
          </span>

          <span class="md-entity-row__expand" aria-hidden="true">
            {{ expandedId === item.id ? '−' : '+' }}
          </span>
        </button>

        <div v-if="expandedId === item.id" class="md-entity-detail">
          <div class="md-compact-grid">
            <label class="md-compact-field">
              <span>事件名称</span>
              <input
                :value="item.name"
                :disabled="readonly"
                @input="updateText(item, 'name', $event)"
              />
            </label>

            <label class="md-compact-field">
              <span>函数标识</span>
              <input
                :value="item.code"
                :disabled="readonly"
                spellcheck="false"
                @input="updateText(item, 'code', $event)"
              />
            </label>

            <label class="md-compact-field">
              <span>返回类型</span>
              <input
                :value="item.returnType"
                :disabled="readonly"
                spellcheck="false"
                placeholder="void"
                @input="updateText(item, 'returnType', $event)"
              />
            </label>

            <label class="md-compact-switch">
              <input
                type="checkbox"
                :checked="item.async"
                :disabled="readonly"
                @change="updateAsync(item, $event)"
              />
              <span>异步函数</span>
            </label>

            <label class="md-compact-field is-wide">
              <span>用途</span>
              <textarea
                :value="item.purpose"
                :disabled="readonly"
                rows="2"
                placeholder="该事件负责执行什么"
                @input="updateText(item, 'purpose', $event)"
              ></textarea>
            </label>
          </div>

          <section class="md-compact-subsection">
            <header>
              <strong>参数</strong>
              <small>{{ item.parameters.length }} 个</small>
              <button
                type="button"
                :disabled="readonly"
                @click="emit('addParameter', model.id, item.id)"
              >
                ＋ 参数
              </button>
            </header>

            <div v-if="item.parameters.length" class="md-parameter-list">
              <div
                v-for="(parameter, parameterIndex) in item.parameters"
                :key="parameter.id"
                class="md-parameter-item"
              >
                <span class="md-parameter-item__index">{{ parameterIndex + 1 }}</span>

                <input
                  :value="parameter.name"
                  :disabled="readonly"
                  placeholder="参数名"
                  @input="updateParameterText(item, parameter, 'name', $event)"
                />

                <input
                  :value="parameter.type"
                  :disabled="readonly"
                  spellcheck="false"
                  placeholder="类型"
                  @input="updateParameterText(item, parameter, 'type', $event)"
                />

                <label title="必填">
                  <input
                    type="checkbox"
                    :checked="parameter.required"
                    :disabled="readonly"
                    @change="updateParameterRequired(item, parameter, $event)"
                  />
                  必填
                </label>

                <button
                  class="is-danger"
                  type="button"
                  :disabled="readonly"
                  title="删除参数"
                  @click="emit('deleteParameter', model.id, item.id, parameter.id)"
                >
                  ×
                </button>

                <input
                  class="md-parameter-item__purpose"
                  :value="parameter.purpose"
                  :disabled="readonly"
                  placeholder="参数用途（可选）"
                  @input="updateParameterText(item, parameter, 'purpose', $event)"
                />
              </div>
            </div>

            <div v-else class="md-compact-empty">无参数</div>
          </section>

          <footer class="md-entity-detail__actions">
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('delete', model.id, item.id)"
            >
              删除事件
            </button>
          </footer>
        </div>
      </article>
    </div>

    <div v-else class="md-entity-empty">
      {{ query ? '没有匹配事件' : '尚未定义事件 / Function' }}
    </div>
  </section>
</template>
