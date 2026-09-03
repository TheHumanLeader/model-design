import { describe, expect, it } from 'vitest'
import {
  GROUP_CONTENT_TOP,
  GROUP_PADDING,
  constrainModelMovement,
  createDemoDocument,
  createEmptyDocument,
  createEventParameter,
  createGroup,
  createGroupAroundModels,
  createModel,
  createModelEvent,
  createModelTrigger,
  fitGroupToContents,
  modelHeight,
  normalizeDocument,
} from '../src/core'

describe('model design document', () => {
  it('creates an empty document', () => {
    expect(createEmptyDocument()).toEqual({
      version: 1,
      models: [],
      groups: [],
    })
  })

  it('creates a demo document with valid relations, events and triggers', () => {
    const document = createDemoDocument()
    const groupIds = new Set(document.groups.map((group) => group.id))
    const modelIds = new Set(document.models.map((model) => model.id))
    const relation = document.models
      .flatMap((model) => model.fields)
      .find((field) => field.relation)?.relation
    const modelWithEvent = document.models.find((model) => model.events.length > 0)

    expect(document.models.length).toBeGreaterThan(0)
    expect(document.groups.length).toBeGreaterThan(0)
    expect(
      document.models.every((model) => !model.groupId || groupIds.has(model.groupId)),
    ).toBe(true)
    expect(relation).not.toBeNull()
    expect(relation && modelIds.has(relation.modelId)).toBe(true)
    expect(modelWithEvent?.events.length).toBeGreaterThan(0)
    expect(modelWithEvent?.triggers[0]?.eventId).toBe(modelWithEvent?.events[0]?.id)
  })

  it('normalizes model tags while creating a model', () => {
    const model = createModel({
      name: '用户',
      tags: [' 核心 ', '核心', 'API', '', 'api'],
    })

    expect(model.tags).toEqual(['核心', 'API'])
  })

  it('creates event signatures and trigger defaults', () => {
    const parameter = createEventParameter({
      name: '用户标识',
      type: 'string',
      required: true,
    })
    const event = createModelEvent({
      name: '加载用户',
      code: 'loadUser',
      parameters: [parameter],
      returnType: 'Promise<User>',
      async: true,
    })
    const trigger = createModelTrigger({
      name: '更新后加载',
      eventId: event.id,
    })
    const model = createModel({
      name: '用户',
      fields: [{ id: 'status', name: '状态' }],
      events: [event],
      triggers: [{ ...trigger, fieldId: 'status' }],
    })

    expect(model.events[0]?.parameters[0]?.required).toBe(true)
    expect(model.events[0]?.returnType).toBe('Promise<User>')
    expect(model.triggers[0]?.source).toBe('update')
    expect(model.triggers[0]?.timing).toBe('after')
    expect(model.triggers[0]?.eventId).toBe(event.id)
    expect(model.triggers[0]?.fieldId).toBe('status')
  })

  it('groups selected models and keeps membership on the model', () => {
    const first = createModel({ name: '用户', x: 100, y: 100 })
    const second = createModel({ name: '权限', x: 420, y: 180 })
    const source = {
      version: 1 as const,
      models: [first, second],
      groups: [],
    }

    const result = createGroupAroundModels(source, [first.id, second.id])

    expect(result.group).not.toBeNull()
    expect(result.document.groups).toHaveLength(1)
    expect(
      result.document.models.every((model) => model.groupId === result.group?.id),
    ).toBe(true)
  })

  it('fits a group around its members', () => {
    const document = createDemoDocument()
    const group = document.groups[0]

    expect(group).toBeDefined()
    if (!group) return

    const next = fitGroupToContents(document, group.id)
    const fitted = next.groups.find((candidate) => candidate.id === group.id)

    expect(fitted).toBeDefined()
    expect(fitted?.width).toBeGreaterThan(0)
    expect(fitted?.height).toBeGreaterThan(0)
  })

  it('constrains grouped model movement to the group content box', () => {
    const group = createGroup({
      x: 100,
      y: 100,
      width: 520,
      height: 420,
    })
    const model = createModel({
      x: 160,
      y: 190,
      groupId: group.id,
      fields: [{ name: '标识', type: 'id' }],
    })
    const document = {
      version: 1 as const,
      models: [model],
      groups: [group],
    }

    const positive = constrainModelMovement(document, [model.id], {
      x: 2000,
      y: 2000,
    })
    const negative = constrainModelMovement(document, [model.id], {
      x: -2000,
      y: -2000,
    })

    expect(model.x + positive.x + model.width).toBeLessThanOrEqual(
      group.x + group.width - GROUP_PADDING,
    )
    expect(model.y + positive.y + modelHeight(model)).toBeLessThanOrEqual(
      group.y + group.height - GROUP_PADDING,
    )
    expect(model.x + negative.x).toBeGreaterThanOrEqual(
      group.x + GROUP_PADDING,
    )
    expect(model.y + negative.y).toBeGreaterThanOrEqual(
      group.y + GROUP_CONTENT_TOP,
    )
  })

  it('leaves root model movement unrestricted', () => {
    const model = createModel({ x: 0, y: 0 })
    const document = {
      version: 1 as const,
      models: [model],
      groups: [],
    }

    expect(
      constrainModelMovement(document, [model.id], { x: 900, y: -700 }),
    ).toEqual({ x: 900, y: -700 })
  })

  it('normalizes legacy flags and missing arrays', () => {
    const document = normalizeDocument({
      models: [
        {
          id: 'model_1',
          name: '用户',
          x: 0,
          y: 0,
          fields: [
            {
              id: 'field_1',
              name: '标识',
              type: 'id',
              primary: true,
            },
          ],
        },
      ],
      groups: [],
    })

    expect(document.models[0]?.tags).toEqual([])
    expect(document.models[0]?.events).toEqual([])
    expect(document.models[0]?.triggers).toEqual([])
    expect(document.models[0]?.fields[0]?.primaryKey).toBe(true)
    expect(document.models[0]?.fields[0]?.relation).toBeNull()
  })

  it('preserves a valid field relation during import', () => {
    const document = normalizeDocument({
      models: [
        {
          id: 'user',
          name: '用户',
          tags: '账户, 核心, 账户',
          fields: [
            {
              id: 'role_id',
              name: '角色标识',
              type: 'id',
              relation: {
                modelId: 'role',
                fieldId: 'id',
                type: 'many-to-one',
                label: '属于角色',
              },
            },
          ],
        },
        {
          id: 'role',
          name: '角色',
          fields: [
            {
              id: 'id',
              name: '标识',
              type: 'id',
              primaryKey: true,
            },
          ],
        },
      ],
      groups: [],
    })

    expect(document.models[0]?.tags).toEqual(['账户', '核心'])
    expect(document.models[0]?.fields[0]?.relation).toEqual({
      modelId: 'role',
      fieldId: 'id',
      type: 'many-to-one',
      label: '属于角色',
    })
  })

  it('normalizes events, parameters and valid trigger references', () => {
    const document = normalizeDocument({
      models: [
        {
          id: 'user',
          fields: [{ id: 'status', name: '状态' }],
          events: [
            {
              id: 'sync',
              name: '同步',
              code: 'sync',
              returnType: 'Promise<void>',
              async: true,
              parameters: [
                {
                  id: 'force',
                  name: '强制',
                  type: 'boolean',
                  required: true,
                },
              ],
            },
          ],
          triggers: [
            {
              id: 'after-status',
              name: '状态变化后同步',
              source: 'field-change',
              timing: 'after',
              fieldId: 'status',
              eventId: 'sync',
              enabled: true,
            },
          ],
        },
      ],
      groups: [],
    })

    const model = document.models[0]
    expect(model?.events[0]?.parameters[0]?.type).toBe('boolean')
    expect(model?.triggers[0]?.fieldId).toBe('status')
    expect(model?.triggers[0]?.eventId).toBe('sync')
  })

  it('cleans dangling trigger references during import', () => {
    const document = normalizeDocument({
      models: [
        {
          id: 'user',
          fields: [{ id: 'status' }],
          events: [{ id: 'save', name: '保存' }],
          triggers: [
            {
              id: 'invalid',
              source: 'update',
              fieldId: 'missing-field',
              eventId: 'missing-event',
            },
            {
              id: 'create',
              source: 'create',
              fieldId: 'status',
              eventId: 'save',
            },
          ],
        },
      ],
      groups: [],
    })

    expect(document.models[0]?.triggers[0]?.fieldId).toBeNull()
    expect(document.models[0]?.triggers[0]?.eventId).toBeNull()
    expect(document.models[0]?.triggers[1]?.fieldId).toBeNull()
    expect(document.models[0]?.triggers[1]?.eventId).toBe('save')
  })

  it('cleans dangling model and field relations during import', () => {
    const missingModel = normalizeDocument({
      models: [
        {
          id: 'user',
          fields: [
            {
              id: 'role_id',
              relation: {
                modelId: 'missing',
                fieldId: null,
                type: 'many-to-one',
              },
            },
          ],
        },
      ],
      groups: [],
    })

    expect(missingModel.models[0]?.fields[0]?.relation).toBeNull()

    const missingField = normalizeDocument({
      models: [
        {
          id: 'user',
          fields: [
            {
              id: 'role_id',
              relation: {
                modelId: 'role',
                fieldId: 'missing-field',
                type: 'many-to-one',
              },
            },
          ],
        },
        {
          id: 'role',
          fields: [],
        },
      ],
      groups: [],
    })

    expect(missingField.models[0]?.fields[0]?.relation?.modelId).toBe('role')
    expect(missingField.models[0]?.fields[0]?.relation?.fieldId).toBeNull()
  })
})
