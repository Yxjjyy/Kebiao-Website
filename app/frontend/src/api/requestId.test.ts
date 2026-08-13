import { describe, expect, it } from 'vitest'
import { createRequestId } from './requestId'

describe('createRequestId', () => {
  it('uses a UUID generator', () => {
    expect(createRequestId(() => 'req-fixed')).toBe('req-fixed')
  })
})
