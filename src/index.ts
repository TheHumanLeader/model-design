import './styles/index.css'

export { default as ModelDesigner } from './components/ModelDesigner.vue'

export * from './core'
export type {
  BuiltInModelFieldType,
  DesignerMenuItem,
  DesignerSelection,
  DesignerTheme,
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelDesignerApi,
  ModelField,
  ModelFieldType,
  ModelGroup,
  ModelNode,
  ModelPatch,
  Point,
  Rect,
} from './types'
export { MODEL_FIELD_TYPES } from './types'
