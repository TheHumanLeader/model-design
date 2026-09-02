<script setup lang="ts" vapor>
import { computed } from 'vue'
import type { ModelGroup } from '../types'

const props = defineProps<{
  group: ModelGroup
  x: number
  y: number
  width: number
  height: number
  memberCount: number
  selected: boolean
  dropTarget: boolean
  moving: boolean
  resizing: boolean
}>()

const emit = defineEmits<{
  select: [groupId: string, event: PointerEvent]
  movestart: [groupId: string, event: PointerEvent]
  resizestart: [groupId: string, event: PointerEvent]
  contextmenu: [groupId: string, event: MouseEvent]
  doubleclick: [groupId: string]
}>()

const groupStyle = computed(() => ({
  '--md-group-x': `${props.x}px`,
  '--md-group-y': `${props.y}px`,
  '--md-group-width': `${props.width}px`,
  '--md-group-height': `${props.height}px`,
}))

function handleSelect(event: PointerEvent): void {
  if (event.button !== 0) return
  emit('select', props.group.id, event)
}

function handleMoveStart(event: PointerEvent): void {
  if (event.button !== 0) return
  emit('movestart', props.group.id, event)
}

function handleResizeStart(event: PointerEvent): void {
  if (event.button !== 0) return
  emit('resizestart', props.group.id, event)
}
</script>

<template>
  <section
    class="md-model-group"
    :class="{
      'is-selected': selected,
      'is-drop-target': dropTarget,
      'is-moving': moving,
      'is-resizing': resizing,
    }"
    :style="groupStyle"
    :data-group-id="group.id"
    @pointerdown.stop="handleSelect"
    @contextmenu.prevent.stop="emit('contextmenu', group.id, $event)"
    @dblclick.stop="emit('doubleclick', group.id)"
  >
    <header
      class="md-model-group__header"
      @pointerdown.stop="handleMoveStart"
    >
      <span class="md-model-group__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M3.5 7.5h6l1.8 2H20.5v8.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"></path>
          <path d="M3.5 7.5V6a2 2 0 0 1 2-2h4l1.8 2h7.2a2 2 0 0 1 2 2v1.5"></path>
        </svg>
      </span>

      <span class="md-model-group__identity">
        <strong>{{ group.name || '未命名分组' }}</strong>
        <small>{{ memberCount }} 个模型</small>
      </span>

      <span class="md-model-group__drag-hint">拖动分组</span>
    </header>

    <p v-if="group.purpose" class="md-model-group__purpose">
      {{ group.purpose }}
    </p>

    <div v-if="memberCount === 0" class="md-model-group__empty">
      将模型拖入此区域，或右键在分组中创建模型
    </div>

    <button
      class="md-model-group__resize"
      type="button"
      title="调整分组大小"
      aria-label="调整分组大小"
      @pointerdown.stop.prevent="handleResizeStart"
      @contextmenu.prevent.stop
    ></button>
  </section>
</template>
