import './styles/index.css'

export { default as ModelDesigner } from './components/ModelDesigner.vue'

export * from './core'
export type {
  BuiltInModelFieldType,
  DesignerMenuItem,
  DesignerSelection,
  EventParameterPatch,
  FieldPatch,
  GroupPatch,
  ModelDesignDocument,
  ModelDesignerApi,
  ModelEvent,
  ModelEventParameter,
  ModelEventPatch,
  ModelField,
  ModelFieldRelation,
  ModelFieldType,
  ModelGroup,
  ModelNode,
  ModelPatch,
  ModelRelationType,
  ModelTrigger,
  ModelTriggerPatch,
  ModelTriggerSource,
  ModelTriggerTiming,
  Point,
  Rect,
} from './types'
export {
  MODEL_FIELD_TYPES,
  MODEL_RELATION_TYPE_LABELS,
  MODEL_RELATION_TYPES,
  MODEL_TRIGGER_SOURCE_LABELS,
  MODEL_TRIGGER_SOURCES,
  MODEL_TRIGGER_TIMING_LABELS,
  MODEL_TRIGGER_TIMINGS,
} from './types'
