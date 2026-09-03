<script setup lang="ts" vapor>
import { createId } from '../core'

export interface RelationLine {
  id: string
  path: string
  label: string
  labelX: number
  labelY: number
  labelWidth: number
  startX: number
  startY: number
  endX: number
  endY: number
}

defineProps<{
  lines: RelationLine[]
}>()

const markerId = createId('md-relation-arrow')
const gradientId = createId('md-relation-gradient')
const glowId = createId('md-relation-glow')
const particleGlowId = createId('md-relation-particle-glow')
</script>

<template>
  <svg class="md-relation-layer" width="1" height="1" overflow="visible" aria-hidden="true">
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="var(--md-accent-2)"></stop>
        <stop offset="0.48" stop-color="var(--md-accent)"></stop>
        <stop offset="1" stop-color="var(--md-success)"></stop>
      </linearGradient>

      <filter :id="glowId" x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="4.5" result="blur"></feGaussianBlur>
        <feMerge>
          <feMergeNode in="blur"></feMergeNode>
          <feMergeNode in="SourceGraphic"></feMergeNode>
        </feMerge>
      </filter>

      <filter :id="particleGlowId" x="-180%" y="-180%" width="460%" height="460%">
        <feGaussianBlur stdDeviation="3" result="particleBlur"></feGaussianBlur>
        <feMerge>
          <feMergeNode in="particleBlur"></feMergeNode>
          <feMergeNode in="SourceGraphic"></feMergeNode>
        </feMerge>
      </filter>

      <marker
        :id="markerId"
        markerWidth="12"
        markerHeight="12"
        refX="9"
        refY="6"
        orient="auto-start-reverse"
        markerUnits="strokeWidth"
      >
        <path class="md-relation-marker" d="M 0 0 L 12 6 L 0 12 L 3.2 6 z"></path>
      </marker>
    </defs>

    <g
      v-for="(line, index) in lines"
      :key="line.id"
      class="md-relation-line"
      :style="{ '--md-edge-delay': `${index * 90}ms` }"
    >
      <circle
        class="md-relation-line__terminal is-source"
        :cx="line.startX"
        :cy="line.startY"
        r="5"
      ></circle>
      <circle
        class="md-relation-line__terminal is-target"
        :cx="line.endX"
        :cy="line.endY"
        r="6"
      ></circle>

      <path class="md-relation-line__halo" :d="line.path"></path>
      <path
        class="md-relation-line__beam"
        :d="line.path"
        pathLength="1"
        :stroke="`url(#${gradientId})`"
        :filter="`url(#${glowId})`"
      ></path>
      <path
        class="md-relation-line__path"
        :d="line.path"
        :stroke="`url(#${gradientId})`"
        :marker-end="`url(#${markerId})`"
      ></path>

      <circle
        class="md-relation-particle is-primary"
        r="3.8"
        :filter="`url(#${particleGlowId})`"
      >
        <animateMotion
          :path="line.path"
          dur="2.55s"
          :begin="`${index * 0.14}s`"
          repeatCount="indefinite"
          rotate="auto"
        ></animateMotion>
      </circle>

      <circle
        class="md-relation-particle is-secondary"
        r="2.2"
        :filter="`url(#${particleGlowId})`"
      >
        <animateMotion
          :path="line.path"
          dur="2.55s"
          :begin="`${index * 0.14 - 1.25}s`"
          repeatCount="indefinite"
          rotate="auto"
        ></animateMotion>
      </circle>

      <g
        class="md-relation-line__label"
        :transform="`translate(${line.labelX} ${line.labelY})`"
      >
        <rect
          :x="-line.labelWidth / 2"
          y="-14"
          :width="line.labelWidth"
          height="28"
          rx="12"
        ></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.label }}</text>
      </g>
    </g>
  </svg>
</template>
