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

  it('creates a demo document with valid group references', () => {
    const document = createDemoDocument()
    const groupIds = new Set(document.groups.map((group) => group.id))

    expect(document.models.length).toBeGreaterThan(0)
    expect(document.groups.length).toBeGreaterThan(0)
    expect(document.models.every((model) => model.groupId && groupIds.has(model.groupId))).toBe(
      true,
    )
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

  it('normalizes legacy primary flags while importing', () => {
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

    expect(document.models[0]?.fields[0]?.primaryKey).toBe(true)
  })
})
