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

export type BuiltInModelFieldType = (typeof MODEL_FIELD_TYPES)[number]
export type ModelFieldType = BuiltInModelFieldType | (string & {})

export interface ModelField {
  id: string
  name: string
  code: string
  type: ModelFieldType
  purpose: string
  required: boolean
  primaryKey: boolean
  unique: boolean
}

export interface ModelNode {
  id: string
  kind: 'model'
  name: string
  code: string
  purpose: string
  x: number
  y: number
  width: number
  groupId: string | null
  fields: ModelField[]
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

export type DesignerTheme = 'light' | 'dark' | 'auto'

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
}
