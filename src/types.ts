export const MODEL_FIELD_TYPES = [
  'string',
  'text',
  'number',
  'boolean',
  'id',
  'date',
  'datetime',
  'enum',
  'array',
  'object',
  'relation',
  'custom',
] as const

export const MODEL_RELATION_TYPES = [
  'one-to-one',
  'one-to-many',
  'many-to-one',
  'many-to-many',
] as const

export const MODEL_TRIGGER_SOURCES = [
  'create',
  'update',
  'delete',
  'field-change',
  'custom',
] as const

export const MODEL_TRIGGER_TIMINGS = ['before', 'after'] as const

export type BuiltInModelFieldType = (typeof MODEL_FIELD_TYPES)[number]
export type ModelFieldType = BuiltInModelFieldType | (string & {})
export type ModelRelationType = (typeof MODEL_RELATION_TYPES)[number]
export type ModelTriggerSource = (typeof MODEL_TRIGGER_SOURCES)[number]
export type ModelTriggerTiming = (typeof MODEL_TRIGGER_TIMINGS)[number]

export const MODEL_RELATION_TYPE_LABELS: Record<ModelRelationType, string> = {
  'one-to-one': '一对一',
  'one-to-many': '一对多',
  'many-to-one': '多对一',
  'many-to-many': '多对多',
}

export const MODEL_TRIGGER_SOURCE_LABELS: Record<ModelTriggerSource, string> = {
  create: '创建',
  update: '更新',
  delete: '删除',
  'field-change': '字段变化',
  custom: '自定义',
}

export const MODEL_TRIGGER_TIMING_LABELS: Record<ModelTriggerTiming, string> = {
  before: '之前',
  after: '之后',
}

export interface ModelFieldRelation {
  modelId: string
  fieldId: string | null
  type: ModelRelationType
  label: string
}

export interface ModelField {
  id: string
  name: string
  code: string
  type: ModelFieldType
  purpose: string
  required: boolean
  primaryKey: boolean
  unique: boolean
  relation: ModelFieldRelation | null
}

export interface ModelEventParameter {
  id: string
  name: string
  type: string
  purpose: string
  required: boolean
}

export interface ModelEvent {
  id: string
  name: string
  code: string
  purpose: string
  parameters: ModelEventParameter[]
  returnType: string
  async: boolean
}

export interface ModelTrigger {
  id: string
  name: string
  source: ModelTriggerSource
  timing: ModelTriggerTiming
  fieldId: string | null
  eventId: string | null
  condition: string
  purpose: string
  enabled: boolean
}

export interface ModelNode {
  id: string
  kind: 'model'
  name: string
  code: string
  purpose: string
  tags: string[]
  x: number
  y: number
  width: number
  groupId: string | null
  fields: ModelField[]
  events: ModelEvent[]
  triggers: ModelTrigger[]
}

export interface ModelGroup {
  id: string
  kind: 'group'
  name: string
  purpose: string
  x: number
  y: number
  width: number
  height: number
}

export interface ModelDesignDocument {
  version: 1
  models: ModelNode[]
  groups: ModelGroup[]
}

export interface DesignerSelection {
  modelIds: string[]
  groupId: string | null
}

export interface ModelDesignerApi {
  createModel(position?: Partial<Point>, groupId?: string | null): string
  createGroup(position?: Partial<Point>): string
  groupSelected(): string | null
  deleteSelected(): void
  clearSelection(): void
  viewRelations(modelId: string): void
  clearRelationView(): void
  undo(): void
  redo(): void
  fitView(): void
  zoomIn(): void
  zoomOut(): void
  exportJSON(): string
  importJSON(source: string): void
  getDocument(): ModelDesignDocument
}

export interface Point {
  x: number
  y: number
}

export interface Rect extends Point {
  width: number
  height: number
}

export interface DesignerMenuItem {
  id: string
  label: string
  hint?: string
  disabled?: boolean
  danger?: boolean
  separatorBefore?: boolean
}

export interface ModelPatch {
  name?: string
  code?: string
  purpose?: string
  tags?: string[]
  groupId?: string | null
}

export interface GroupPatch {
  name?: string
  purpose?: string
}

export interface FieldPatch {
  name?: string
  code?: string
  type?: ModelFieldType
  purpose?: string
  required?: boolean
  primaryKey?: boolean
  unique?: boolean
  relation?: ModelFieldRelation | null
}

export interface ModelEventPatch {
  name?: string
  code?: string
  purpose?: string
  returnType?: string
  async?: boolean
}

export interface EventParameterPatch {
  name?: string
  type?: string
  purpose?: string
  required?: boolean
}

export interface ModelTriggerPatch {
  name?: string
  source?: ModelTriggerSource
  timing?: ModelTriggerTiming
  fieldId?: string | null
  eventId?: string | null
  condition?: string
  purpose?: string
  enabled?: boolean
}
