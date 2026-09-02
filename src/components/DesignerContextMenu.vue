<script setup lang="ts" vapor>
import { computed } from 'vue'
import type { DesignerMenuItem } from '../types'

const props = defineProps<{
  open: boolean
  x: number
  y: number
  items: DesignerMenuItem[]
}>()

const emit = defineEmits<{
  select: [itemId: string]
}>()

const menuStyle = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`,
}))

function selectItem(item: DesignerMenuItem): void {
  if (item.disabled) return
  emit('select', item.id)
}
</script>

<template>
  <div
    v-if="open"
    class="md-context-menu"
    :style="menuStyle"
    role="menu"
    @pointerdown.stop
    @contextmenu.prevent.stop
  >
    <template v-for="item in items" :key="item.id">
      <div
        v-if="item.separatorBefore"
        class="md-context-menu__separator"
        role="separator"
      ></div>

      <button
        class="md-context-menu__item"
        :class="{ 'is-danger': item.danger }"
        type="button"
        role="menuitem"
        :disabled="item.disabled"
        @click="selectItem(item)"
      >
        <span>{{ item.label }}</span>
        <kbd v-if="item.hint">{{ item.hint }}</kbd>
      </button>
    </template>
  </div>
</template>
