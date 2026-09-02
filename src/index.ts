import './styles/index.css'

export { default as ModelDesigner } from './components/ModelDesigner.vue'

export * from './core'
export type {
  BuiltInModelFieldType,
  DesignerMenuItem,
  DesignerSelection,
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelDesignerApi,
  ModelField,
  ModelFieldRelation,
  ModelFieldType,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelRelationType,
  Point,
  Rect,
} from './types'
export {
  MODEL_FIELD_TYPES,
  MODEL_RELATION_TYPE_LABELS,
  MODEL_RELATION_TYPES,
} from './types'
