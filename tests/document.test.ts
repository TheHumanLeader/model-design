import { describe, expect, it } from 'vitest'
import {
  createDemoDocument,
  createEmptyDocument,
  createGroupAroundModels,
  createModel,
  fitGroupToContents,
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

  it('creates a demo document with valid group and field relations', () => {
    const document = createDemoDocument()
    const groupIds = new Set(document.groups.map((group) => group.id))
    const modelIds = new Set(document.models.map((model) => model.id))
    const relation = document.models
      .flatMap((model) => model.fields)
      .find((field) => field.relation)?.relation

    expect(document.models.length).toBeGreaterThan(0)
    expect(document.groups.length).toBeGreaterThan(0)
    expect(
      document.models.every((model) => !model.groupId || groupIds.has(model.groupId)),
    ).toBe(true)
    expect(relation).not.toBeNull()
    expect(relation && modelIds.has(relation.modelId)).toBe(true)
  })

  it('normalizes model tags while creating a model', () => {
    const model = createModel({
      name: '用户',
      tags: [' 核心 ', '核心', 'API', '', 'api'],
    })

    expect(model.tags).toEqual(['核心', 'API'])
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

  it('normalizes legacy primary flags and missing tag/relation values', () => {
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
