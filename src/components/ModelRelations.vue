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
  sourceCardinality: '1' | 'N'
  targetCardinality: '1' | 'N'
}

defineProps<{
  lines: RelationLine[]
}>()

const sourceMarkerId = createId('md-relation-arrow-source')
const targetMarkerId = createId('md-relation-arrow-target')
const gradientId = createId('md-relation-gradient')
const glowId = createId('md-relation-glow')
const particleGlowId = createId('md-relation-particle-glow')

function isOneToOne(line: RelationLine): boolean {
  return line.sourceCardinality === '1' && line.targetCardinality === '1'
}

function displayLabel(line: RelationLine): string {
  const base = line.label
    .replace(/\s*·\s*[1N]\s*[→↔]\s*[1N]\s*$/, '')
    .trim()
  const arrow = isOneToOne(line) ? '↔' : '→'

  return `${base || '关系'} · ${line.sourceCardinality} ${arrow} ${line.targetCardinality}`
}
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
        :id="sourceMarkerId"
        markerWidth="12"
        markerHeight="12"
        refX="9"
        refY="6"
        orient="auto-start-reverse"
        markerUnits="strokeWidth"
      >
        <path
          class="md-relation-marker is-source"
          d="M 0 0 L 12 6 L 0 12 L 3.2 6 z"
        ></path>
      </marker>

      <marker
        :id="targetMarkerId"
        markerWidth="12"
        markerHeight="12"
        refX="9"
        refY="6"
        orient="auto-start-reverse"
        markerUnits="strokeWidth"
      >
        <path
          class="md-relation-marker is-target"
          d="M 0 0 L 12 6 L 0 12 L 3.2 6 z"
        ></path>
      </marker>
    </defs>

    <g
      v-for="(line, index) in lines"
      :key="line.id"
      class="md-relation-line"
      :class="{ 'is-one-to-one': isOneToOne(line) }"
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

      <g
        class="md-relation-cardinality is-source"
        :transform="`translate(${line.startX + (line.endX >= line.startX ? 16 : -16)} ${line.startY - 13})`"
      >
        <rect x="-10" y="-8" width="20" height="16" rx="8"></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.sourceCardinality }}</text>
      </g>
      <g
        class="md-relation-cardinality is-target"
        :transform="`translate(${line.endX + (line.endX >= line.startX ? -16 : 16)} ${line.endY - 13})`"
      >
        <rect x="-10" y="-8" width="20" height="16" rx="8"></rect>
        <text text-anchor="middle" dominant-baseline="central">{{ line.targetCardinality }}</text>
      </g>

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
        :marker-start="isOneToOne(line) ? `url(#${sourceMarkerId})` : undefined"
        :marker-end="`url(#${targetMarkerId})`"
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
        v-if="isOneToOne(line)"
        class="md-relation-particle is-reverse"
        r="3.2"
        :filter="`url(#${particleGlowId})`"
      >
        <animateMotion
          :path="line.path"
          keyPoints="1;0"
          keyTimes="0;1"
          calcMode="linear"
          dur="2.55s"
          :begin="`${index * 0.14 - 1.25}s`"
          repeatCount="indefinite"
          rotate="auto"
        ></animateMotion>
      </circle>

      <circle
        v-else
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
        <text text-anchor="middle" dominant-baseline="central">
          {{ displayLabel(line) }}
        </text>
      </g>
    </g>
  </svg>
</template>
