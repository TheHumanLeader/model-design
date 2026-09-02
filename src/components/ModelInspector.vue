<script setup lang="ts" vapor>
import { computed } from 'vue'
import { MODEL_FIELD_TYPES } from '../types'
import type {
  FieldPatch,
  GroupPatch,
  ModelField,
  ModelGroup,
  ModelNode,
  ModelPatch,
} from '../types'

const props = defineProps<{
  models: ModelNode[]
  group: ModelGroup | null
  groups: ModelGroup[]
  groupMemberCount: number
  readonly: boolean
}>()

const emit = defineEmits<{
  updateModel: [modelId: string, patch: ModelPatch, mergeKey?: string]
  updateGroup: [groupId: string, patch: GroupPatch, mergeKey?: string]
  addField: [modelId: string]
  updateField: [modelId: string, fieldId: string, patch: FieldPatch, mergeKey?: string]
  deleteField: [modelId: string, fieldId: string]
  duplicateModels: [modelIds: string[]]
  deleteModels: [modelIds: string[]]
  groupModels: [modelIds: string[]]
  deleteGroup: [groupId: string]
  ungroup: [groupId: string]
  fitGroup: [groupId: string]
}>()

const model = computed(() => (props.models.length === 1 ? props.models[0] ?? null : null))
const isMultiple = computed(() => props.models.length > 1)

const modelPath = computed(() => {
  const current = model.value
  if (!current) return ''

  const group = props.groups.find((candidate) => candidate.id === current.groupId)
  return group ? `根画板 / ${group.name} / ${current.name}` : `根画板 / ${current.name}`
})

function textValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLTextAreaElement).value
}

function checkedValue(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function updateModelText(
  current: ModelNode,
  key: 'name' | 'code' | 'purpose',
  event: Event,
): void {
  emit(
    'updateModel',
    current.id,
    { [key]: textValue(event) },
    `model:${current.id}:${key}`,
  )
}

function updateModelGroup(current: ModelNode, event: Event): void {
  emit('updateModel', current.id, {
    groupId: textValue(event) || null,
  })
}

function updateGroupText(
  current: ModelGroup,
  key: 'name' | 'purpose',
  event: Event,
): void {
  emit(
    'updateGroup',
    current.id,
    { [key]: textValue(event) },
    `group:${current.id}:${key}`,
  )
}

function updateFieldText(
  currentModel: ModelNode,
  field: ModelField,
  key: 'name' | 'code' | 'purpose' | 'type',
  event: Event,
): void {
  emit(
    'updateField',
    currentModel.id,
    field.id,
    { [key]: textValue(event) },
    `field:${field.id}:${key}`,
  )
}

function updateFieldFlag(
  currentModel: ModelNode,
  field: ModelField,
  key: 'required' | 'primaryKey' | 'unique',
  event: Event,
): void {
  emit('updateField', currentModel.id, field.id, {
    [key]: checkedValue(event),
  })
}
</script>

<template>
  <aside class="md-inspector">
    <header class="md-inspector__header">
      <div>
        <strong>
          {{
            model
              ? '模型配置'
              : group
                ? '分组配置'
                : isMultiple
                  ? '批量选择'
                  : '模型设计器'
          }}
        </strong>
        <p>
          {{
            model
              ? '定义模型用途、字段与字段用途'
              : group
                ? '定义分组用途与模型归属'
                : isMultiple
                  ? `已选择 ${models.length} 个模型`
                  : '选择画板中的模型或分组进行配置'
          }}
        </p>
      </div>

      <span v-if="model" class="md-inspector__type">模型</span>
      <span v-else-if="group" class="md-inspector__type">分组</span>
    </header>

    <div class="md-inspector__body">
      <template v-if="model">
        <section class="md-inspector__section">
          <h3>模型信息</h3>

          <label class="md-form-item">
            <span>模型名称</span>
            <input
              :value="model.name"
              :disabled="readonly"
              placeholder="例如：用户模型"
              @input="updateModelText(model, 'name', $event)"
            />
          </label>

          <label class="md-form-item">
            <span>
              模型标识
              <small>用于代码、表名或接口标识</small>
            </span>
            <input
              :value="model.code"
              :disabled="readonly"
              spellcheck="false"
              placeholder="例如：user"
              @input="updateModelText(model, 'code', $event)"
            />
          </label>

          <label class="md-form-item">
            <span>
              模型用途
              <small>该模型负责表达什么</small>
            </span>
            <textarea
              :value="model.purpose"
              :disabled="readonly"
              rows="3"
              placeholder="描述模型的职责、边界与使用场景"
              @input="updateModelText(model, 'purpose', $event)"
            ></textarea>
          </label>

          <label class="md-form-item">
            <span>所属分组</span>
            <select
              :value="model.groupId || ''"
              :disabled="readonly"
              @change="updateModelGroup(model, $event)"
            >
              <option value="">根画板</option>
              <option
                v-for="candidate in groups"
                :key="candidate.id"
                :value="candidate.id"
              >
                {{ candidate.name }}
              </option>
            </select>
          </label>

          <div class="md-inspector__path" :title="modelPath">
            {{ modelPath }}
          </div>
        </section>

        <section class="md-inspector__section">
          <div class="md-inspector__section-title">
            <h3>字段配置</h3>
            <span>{{ model.fields.length }} 个字段</span>
          </div>

          <div v-if="model.fields.length" class="md-field-list">
            <article
              v-for="(field, index) in model.fields"
              :key="field.id"
              class="md-field-card"
            >
              <header class="md-field-card__header">
                <strong>{{ field.name || `字段 ${index + 1}` }}</strong>
                <button
                  type="button"
                  :disabled="readonly"
                  title="删除字段"
                  @click="emit('deleteField', model.id, field.id)"
                >
                  删除
                </button>
              </header>

              <div class="md-field-card__grid">
                <label class="md-form-item">
                  <span>字段名称</span>
                  <input
                    :value="field.name"
                    :disabled="readonly"
                    placeholder="例如：用户标识"
                    @input="updateFieldText(model, field, 'name', $event)"
                  />
                </label>

                <label class="md-form-item">
                  <span>字段标识</span>
                  <input
                    :value="field.code"
                    :disabled="readonly"
                    spellcheck="false"
                    placeholder="例如：user_id"
                    @input="updateFieldText(model, field, 'code', $event)"
                  />
                </label>

                <label class="md-form-item">
                  <span>字段类型</span>
                  <select
                    :value="field.type"
                    :disabled="readonly"
                    @change="updateFieldText(model, field, 'type', $event)"
                  >
                    <option
                      v-for="fieldType in MODEL_FIELD_TYPES"
                      :key="fieldType"
                      :value="fieldType"
                    >
                      {{ fieldType }}
                    </option>
                  </select>
                </label>

                <label class="md-form-item md-form-item--wide">
                  <span>字段用途</span>
                  <textarea
                    :value="field.purpose"
                    :disabled="readonly"
                    rows="2"
                    placeholder="描述字段记录的内容与使用目的"
                    @input="updateFieldText(model, field, 'purpose', $event)"
                  ></textarea>
                </label>
              </div>

              <div class="md-field-card__flags">
                <label>
                  <input
                    type="checkbox"
                    :checked="field.required"
                    :disabled="readonly"
                    @change="updateFieldFlag(model, field, 'required', $event)"
                  />
                  必填
                </label>

                <label>
                  <input
                    type="checkbox"
                    :checked="field.primaryKey"
                    :disabled="readonly"
                    @change="updateFieldFlag(model, field, 'primaryKey', $event)"
                  />
                  主键
                </label>

                <label>
                  <input
                    type="checkbox"
                    :checked="field.unique"
                    :disabled="readonly"
                    @change="updateFieldFlag(model, field, 'unique', $event)"
                  />
                  唯一
                </label>
              </div>
            </article>
          </div>

          <button
            class="md-dashed-button"
            type="button"
            :disabled="readonly"
            @click="emit('addField', model.id)"
          >
            ＋ 添加字段
          </button>
        </section>

        <section class="md-inspector__section">
          <h3>模型操作</h3>
          <div class="md-inspector__actions">
            <button
              type="button"
              :disabled="readonly"
              @click="emit('duplicateModels', [model.id])"
            >
              复制模型
            </button>
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('deleteModels', [model.id])"
            >
              删除模型
            </button>
          </div>
        </section>
      </template>

      <template v-else-if="group">
        <section class="md-inspector__section">
          <h3>分组信息</h3>

          <label class="md-form-item">
            <span>分组名称</span>
            <input
              :value="group.name"
              :disabled="readonly"
              placeholder="例如：用户与权限"
              @input="updateGroupText(group, 'name', $event)"
            />
          </label>

          <label class="md-form-item">
            <span>
              分组用途
              <small>该分组包含哪一类模型</small>
            </span>
            <textarea
              :value="group.purpose"
              :disabled="readonly"
              rows="4"
              placeholder="描述分组的职责与边界"
              @input="updateGroupText(group, 'purpose', $event)"
            ></textarea>
          </label>

          <div class="md-inspector__metric-grid">
            <div>
              <span>模型数量</span>
              <strong>{{ groupMemberCount }}</strong>
            </div>
            <div>
              <span>分组宽度</span>
              <strong>{{ Math.round(group.width) }}</strong>
            </div>
            <div>
              <span>分组高度</span>
              <strong>{{ Math.round(group.height) }}</strong>
            </div>
          </div>
        </section>

        <section class="md-inspector__section">
          <h3>分组操作</h3>
          <div class="md-inspector__actions">
            <button
              type="button"
              :disabled="readonly"
              @click="emit('fitGroup', group.id)"
            >
              适配内容
            </button>
            <button
              type="button"
              :disabled="readonly"
              @click="emit('ungroup', group.id)"
            >
              解散分组
            </button>
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('deleteGroup', group.id)"
            >
              删除分组
            </button>
          </div>
        </section>
      </template>

      <template v-else-if="isMultiple">
        <section class="md-inspector__section">
          <div class="md-multi-selection">
            <span>{{ models.length }}</span>
            <strong>个模型已被选中</strong>
            <p>拖动任意已选模型可整体移动，也可将它们组成一个新分组。</p>
          </div>

          <div class="md-inspector__actions">
            <button
              type="button"
              :disabled="readonly"
              @click="emit('groupModels', models.map((item) => item.id))"
            >
              组成分组
            </button>
            <button
              type="button"
              :disabled="readonly"
              @click="emit('duplicateModels', models.map((item) => item.id))"
            >
              复制所选
            </button>
            <button
              class="is-danger"
              type="button"
              :disabled="readonly"
              @click="emit('deleteModels', models.map((item) => item.id))"
            >
              删除所选
            </button>
          </div>
        </section>
      </template>

      <template v-else>
        <section class="md-inspector__empty">
          <span class="md-inspector__empty-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <rect x="3.5" y="3.5" width="7" height="7" rx="2"></rect>
              <rect x="13.5" y="3.5" width="7" height="7" rx="2"></rect>
              <rect x="3.5" y="13.5" width="7" height="7" rx="2"></rect>
              <path d="M17 13.5v7M13.5 17h7"></path>
            </svg>
          </span>
          <strong>从画板开始设计</strong>
          <p>右键画板创建模型或分组，选择模型后即可配置字段及用途。</p>

          <div class="md-inspector__tips">
            <span><kbd>右键</kbd> 创建内容</span>
            <span><kbd>Ctrl</kbd> 多选模型</span>
            <span><kbd>Space</kbd> 拖动画板</span>
            <span><kbd>Delete</kbd> 删除所选</span>
          </div>
        </section>
      </template>
    </div>
  </aside>
</template>
