<script setup lang="ts" vapor>
import { shallowRef } from 'vue'
import ModelDesigner from '../components/ModelDesigner.vue'
import { createDemoDocument, normalizeDocument } from '../core'
import type { ModelDesignDocument } from '../types'

const STORAGE_KEY = 'model-design-playground-v2'

const documentModel = shallowRef<ModelDesignDocument>(loadDocument())

function loadDocument(): ModelDesignDocument {
  try {
    const source = window.localStorage.getItem(STORAGE_KEY)
    return source ? normalizeDocument(JSON.parse(source) as unknown) : createDemoDocument()
  } catch {
    return createDemoDocument()
  }
}

function saveDocument(document: ModelDesignDocument): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(document))
  } catch {
    // Playground persistence is optional; the component itself remains usable.
  }
}
</script>

<template>
  <ModelDesigner
    v-model="documentModel"
    height="100dvh"
    @change="saveDocument"
  />
</template>
