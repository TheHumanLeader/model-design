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
  return props.model.fields.filter((field) => ids.has(field.id))
})

const visibleFields = computed(() => detailFields.value.slice(0, 6))
const hiddenFieldCount = computed(() =>
  Math.max(0, detailFields.value.length - visibleFields.value.length),
)
const visibleTags = computed(() => (props.model.tags ?? []).slice(0, 2))
const hiddenTagCount = computed(() =>
  Math.max(0, (props.model.tags ?? []).length - visibleTags.value.length),
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
    :data-relation-field-count="detail ? detailFields.length : undefined"
    @pointerdown.stop="handlePointerDown"
    @contextmenu.prevent.stop="handleContextMenu"
    @dblclick.stop="handleDoubleClick"
  >
    <header class="md-model-node__header">
      <span class="md-model-node__mark" aria-hidden="true"></span>

      <span class="md-model-node__title-wrap">
        <strong class="md-model-node__title">{{ model.name || '未命名模型' }}</strong>
        <span class="md-model-node__code">{{ model.code || 'unnamed_model' }}</span>
      </span>

      <span v-if="detail" class="md-model-node__role">
        <i></i>
        {{ relationState === 'focus' ? '焦点' : '关联' }}
        <b>{{ detailFields.length }}</b>
      </span>

      <button
        v-else-if="interactive"
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
    </header>

    <template v-if="!detail">
      <p class="md-model-node__purpose">
        {{ model.purpose || '未填写模型用途' }}
      </p>

      <div class="md-model-node__meta">
        <span class="md-model-node__tag-list">
          <template v-if="visibleTags.length">
            <span v-for="tag in visibleTags" :key="tag" class="md-model-node__tag">
              {{ tag }}
            </span>
            <span v-if="hiddenTagCount" class="md-model-node__tag is-more">
              +{{ hiddenTagCount }}
            </span>
          </template>
          <span v-else class="md-model-node__tag-empty">无标签</span>
        </span>

        <span class="md-model-node__metrics">
          <b title="字段">F {{ model.fields.length }}</b>
          <b title="事件 / Function">Fn {{ model.events.length }}</b>
          <b title="触发器">T {{ model.triggers.length }}</b>
          <b v-if="relationCount" title="关系">R {{ relationCount }}</b>
        </span>
      </div>
    </template>

    <div v-else class="md-model-node__fields">
      <template v-if="visibleFields.length">
        <div
          v-for="field in visibleFields"
          :key="field.id"
          class="md-model-node__field"
          :data-field-id="field.id"
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
        关联模型整体
      </div>
    </div>
  </article>
</template>
