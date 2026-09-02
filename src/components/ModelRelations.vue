<script setup lang="ts" vapor>
import { createId } from '../core'

interface RelationLine {
  id: string
  path: string
  label: string
  labelX: number
  labelY: number
  labelWidth: number
}

defineProps<{
  lines: RelationLine[]
}>()

const markerId = createId('md-relation-arrow')
</script>

<template>
  <svg class="md-relation-layer" width="1" height="1" overflow="visible" aria-hidden="true">
    <defs>
      <marker
        :id="markerId"
        markerWidth="10"
        markerHeight="10"
        refX="8"
        refY="5"
        orient="auto-start-reverse"
        markerUnits="strokeWidth"
      >
        <path class="md-relation-marker" d="M 0 0 L 10 5 L 0 10 z"></path>
      </marker>
    </defs>

    <g v-for="line in lines" :key="line.id" class="md-relation-line">
      <path class="md-relation-line__halo" :d="line.path"></path>
      <path
        class="md-relation-line__path"
        :d="line.path"
        :marker-end="`url(#${markerId})`"
      ></path>

      <g
        class="md-relation-line__label"
        :transform="`translate(${line.labelX} ${line.labelY})`"
      >
        <rect
          :x="-line.labelWidth / 2"
          y="-12"
          :width="line.labelWidth"
          height="24"
          rx="10"
        ></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.label }}</text>
      </g>
    </g>
  </svg>
</template>
