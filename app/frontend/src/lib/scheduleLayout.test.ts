import { describe, expect, it } from 'vitest'
import { computeLessonLanes } from './scheduleLayout'

describe('computeLessonLanes', () => {
  it('keeps non-overlapping lessons full width', () => {
    const lanes = computeLessonLanes([
      { id: 1, start_time: '09:00', duration_hours: 1 },
      { id: 2, start_time: '10:00', duration_hours: 1 },
    ])

    expect(lanes.get(1)).toMatchObject({ lane: 0, lanes: 1, left: 0, width: 100 })
    expect(lanes.get(2)).toMatchObject({ lane: 0, lanes: 1, left: 0, width: 100 })
  })

  it('places overlapping lessons side by side', () => {
    const lanes = computeLessonLanes([
      { id: 1, start_time: '09:00', duration_hours: 2 },
      { id: 2, start_time: '09:30', duration_hours: 1 },
      { id: 3, start_time: '10:30', duration_hours: 1 },
    ])

    expect(lanes.get(1)).toMatchObject({ lane: 0, lanes: 2, width: 50 })
    expect(lanes.get(2)).toMatchObject({ lane: 1, lanes: 2, width: 50 })
    expect(lanes.get(3)).toMatchObject({ lane: 1, lanes: 2, width: 50 })
  })

  it('reuses a lane once the previous lesson has ended', () => {
    const lanes = computeLessonLanes([
      { id: 1, start_time: '09:00', duration_hours: 1 },
      { id: 2, start_time: '09:30', duration_hours: 1 },
      { id: 3, start_time: '10:30', duration_hours: 1 },
    ])

    expect(lanes.get(1)?.lanes).toBe(2)
    expect(lanes.get(2)?.lanes).toBe(2)
    expect(lanes.get(3)).toMatchObject({ lane: 0, lanes: 1, width: 100 })
  })
})
