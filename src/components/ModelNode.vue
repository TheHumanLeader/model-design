<script setup lang="ts" vapor>
import { computed } from 'vue'
import { modelHeight, relationModelHeight } from '../core'
import type { ModelField, ModelNode } from '../types'

const props = withDefaults(
  defineProps<{
    model: ModelNode
    x: number
    y: number
    selected: boolean
    dragging: boolean
    relationState: 'none' | 'focus' | 'related' | 'dimmed'
    relationCount: number
    detail?: boolean
    detailFieldIds?: string[]
    appearanceIndex?: number
    interactive?: boolean
  }>(),
  {
    detail: false,
    detailFieldIds: () => [],
    appearanceIndex: 0,
    interactive: true,
  },
)

const emit = defineEmits<{
  pointerdown: [modelId: string, event: PointerEvent]
  contextmenu: [modelId: string, event: MouseEvent]
  menu: [modelId: string, event: MouseEvent]
  doubleclick: [modelId: string]
}>()

const detailFields = computed<ModelField[]>(() => {
  if (!props.detail) return []

  const ids = new Set(props.detailFieldIds)
  if (ids.size > 0) {
    return props.model.fields.filter((field) => ids.has(field.id))
  }

  return props.model.fields.filter((field) => field.relation)
})

const visibleFields = computed(() => detailFields.value.slice(0, 6))
const hiddenFieldCount = computed(() =>
  Math.max(0, detailFields.value.length - visibleFields.value.length),
)
const visibleTags = computed(() => (props.model.tags ?? []).slice(0, 3))
const hiddenTagCount = computed(() =>
  Math.max(0, (props.model.tags ?? []).length - 3),
)
const nodeHeight = computed(() =>
  props.detail
    ? relationModelHeight(props.model, detailFields.value.length)
    : modelHeight(props.model),
)

const nodeStyle = computed(() => ({
  '--md-node-x': `${props.x}px`,
  '--md-node-y': `${props.y}px`,
  '--md-node-width': `${props.model.width}px`,
  '--md-node-height': `${nodeHeight.value}px`,
  '--md-relation-delay': `${Math.min(props.appearanceIndex, 12) * 72}ms`,
}))

function handlePointerDown(event: PointerEvent): void {
  if (!props.interactive) return
  emit('pointerdown', props.model.id, event)
}

function handleContextMenu(event: MouseEvent): void {
  if (!props.interactive) return
  emit('contextmenu', props.model.id, event)
}

function handleMenu(event: MouseEvent): void {
  if (!props.interactive) return
  emit('menu', props.model.id, event)
}

function handleDoubleClick(): void {
  if (!props.interactive) return
  emit('doubleclick', props.model.id)
}
</script>

<template>
  <article
    class="md-model-node"
    :class="{
      'is-selected': selected,
      'is-dragging': dragging,
      'is-relation-card': detail,
      'is-relation-focus': relationState === 'focus',
      'is-relation-related': relationState === 'related',
      'is-relation-dimmed': relationState === 'dimmed',
      'is-static': !interactive,
    }"
    :style="nodeStyle"
    :data-model-id="model.id"
    @pointerdown.stop="handlePointerDown"
    @contextmenu.prevent.stop="handleContextMenu"
    @dblclick.stop="handleDoubleClick"
  >
    <div class="md-model-node__accent"></div>

    <header class="md-model-node__header">
      <span class="md-model-node__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <rect x="5" y="4" width="14" height="16" rx="3"></rect>
          <path d="M8.5 8h7M8.5 12h7M8.5 16h4"></path>
        </svg>
      </span>

      <span class="md-model-node__title-wrap">
        <strong class="md-model-node__title">{{ model.name || '未命名模型' }}</strong>
        <span class="md-model-node__code">{{ model.code || 'unnamed_model' }}</span>
      </span>

      <button
        v-if="interactive"
        class="md-model-node__menu"
        type="button"
        title="模型菜单"
        aria-label="打开模型菜单"
        @pointerdown.stop
        @click.stop="handleMenu"
        @contextmenu.prevent.stop="handleMenu"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      <span v-else class="md-model-node__signal" aria-hidden="true">
        <i></i><i></i><i></i>
      </span>
    </header>

    <p class="md-model-node__purpose">
      {{ model.purpose || '选择模型，在右侧配置字段、事件与触发器。' }}
    </p>

    <div v-if="visibleTags.length" class="md-model-node__tags">
      <span v-for="tag in visibleTags" :key="tag" class="md-model-node__tag">{{ tag }}</span>
      <span v-if="hiddenTagCount" class="md-model-node__tag is-more">+{{ hiddenTagCount }}</span>
    </div>

    <div v-if="detail" class="md-model-node__relation-context">
      <span>
        <i></i>
        {{ relationState === 'focus' ? 'FOCUS MODEL' : 'RELATED MODEL' }}
      </span>
      <small>
        {{
          detailFields.length
            ? `${detailFields.length} 个关系字段`
            : '模型级关系'
        }}
      </small>
    </div>

    <div v-if="detail" class="md-model-node__fields">
      <template v-if="visibleFields.length">
        <div
          v-for="field in visibleFields"
          :key="field.id"
          class="md-model-node__field"
        >
          <span class="md-model-node__field-name">
            <span v-if="field.primaryKey" class="md-model-node__key" title="主键">◆</span>
            <span v-if="field.relation" class="md-model-node__relation-icon" title="关系字段">↗</span>
            <span class="md-model-node__field-copy">
              <strong>{{ field.name || '未命名字段' }}</strong>
              <small>{{ field.code || 'unnamed_field' }}</small>
            </span>
            <span v-if="field.required" class="md-model-node__required">*</span>
          </span>
          <code>{{ field.type }}</code>
        </div>

        <div v-if="hiddenFieldCount" class="md-model-node__field-more">
          还有 {{ hiddenFieldCount }} 个相关字段
        </div>
      </template>

      <div v-else class="md-model-node__empty">
        关系指向模型整体，没有指定目标字段
      </div>
    </div>

    <footer class="md-model-node__footer">
      <span>{{ model.groupId ? '已加入分组' : '根画板' }}</span>
      <span class="md-model-node__metrics">
        <b title="字段">F {{ model.fields.length }}</b>
        <b title="事件 / Function">Fn {{ model.events.length }}</b>
        <b title="触发器">T {{ model.triggers.length }}</b>
        <b v-if="relationCount" title="关系">R {{ relationCount }}</b>
      </span>
    </footer>
  </article>
</template>
