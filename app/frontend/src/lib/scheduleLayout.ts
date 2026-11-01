export interface LayoutLesson {
  id: number
  start_time: string
  duration_hours: number
}

export interface LessonLane {
  lane: number
  lanes: number
  left: number
  width: number
}

function startMinutes(lesson: LayoutLesson): number {
  const [hour, minute] = lesson.start_time.split(':').map(Number)
  return hour * 60 + minute
}

function endMinutes(lesson: LayoutLesson): number {
  return startMinutes(lesson) + Math.round(lesson.duration_hours * 60)
}

export function computeLessonLanes(lessons: LayoutLesson[]): Map<number, LessonLane> {
  const sorted = [...lessons].sort((a, b) =>
    startMinutes(a) - startMinutes(b)
    || endMinutes(a) - endMinutes(b)
    || a.id - b.id
  )
  const result = new Map<number, LessonLane>()
  let cluster: LayoutLesson[] = []
  let clusterEnd = -1

  function flushCluster() {
    if (!cluster.length) return
    const laneEnds: number[] = []
    const assignments = new Map<number, number>()

    for (const lesson of cluster) {
      const start = startMinutes(lesson)
      let lane = laneEnds.findIndex(end => end <= start)
      if (lane === -1) {
        lane = laneEnds.length
        laneEnds.push(endMinutes(lesson))
      } else {
        laneEnds[lane] = endMinutes(lesson)
      }
      assignments.set(lesson.id, lane)
    }

    const laneCount = Math.max(1, laneEnds.length)
    for (const lesson of cluster) {
      const lane = assignments.get(lesson.id) ?? 0
      result.set(lesson.id, {
        lane,
        lanes: laneCount,
        left: (lane / laneCount) * 100,
        width: 100 / laneCount,
      })
    }
    cluster = []
    clusterEnd = -1
  }

  for (const lesson of sorted) {
    const start = startMinutes(lesson)
    if (cluster.length && start >= clusterEnd) flushCluster()
    cluster.push(lesson)
    clusterEnd = Math.max(clusterEnd, endMinutes(lesson))
  }
  flushCluster()
  return result
}
