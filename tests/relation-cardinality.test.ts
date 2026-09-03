import { describe, expect, it } from 'vitest'
import {
  MODEL_RELATION_CARDINALITIES,
  MODEL_RELATION_TYPE_LABELS,
} from '../src/types'

describe('relationship cardinality semantics', () => {
  it.each([
    ['one-to-one', ['1', '1'], '一对一'],
    ['one-to-many', ['1', 'N'], '一对多'],
    ['many-to-one', ['N', '1'], '多对一'],
    ['many-to-many', ['N', 'N'], '多对多'],
  ] as const)('maps %s from source to target', (type, expected, label) => {
    expect(MODEL_RELATION_CARDINALITIES[type]).toEqual(expected)
    expect(MODEL_RELATION_TYPE_LABELS[type]).toBe(label)
  })
})
