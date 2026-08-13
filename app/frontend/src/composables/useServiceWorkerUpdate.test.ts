import { describe, expect, it, vi } from 'vitest'
import { createServiceWorkerUpdateCoordinator } from './useServiceWorkerUpdate'

function worker(state: ServiceWorkerState = 'installed') {
  const listeners = new Map<string, () => void>()
  return {
    state,
    postMessage: vi.fn(),
    addEventListener: vi.fn((name: string, listener: () => void) => listeners.set(name, listener)),
    dispatch(name: string) { listeners.get(name)?.() },
  }
}

it('shows a waiting update without activating automatically', () => {
  const waiting = worker()
  const coordinator = createServiceWorkerUpdateCoordinator()
  coordinator.observe({ waiting, addEventListener: vi.fn() } as never)

  expect(coordinator.updateAvailable.value).toBe(true)
  expect(waiting.postMessage).not.toHaveBeenCalled()
})

it('activates and reloads at most once after user confirmation', () => {
  const waiting = worker()
  const reload = vi.fn()
  let controllerChange!: () => void
  const container = {
    controller: {},
    addEventListener: vi.fn((_name: string, callback: () => void) => { controllerChange = callback }),
  }
  const coordinator = createServiceWorkerUpdateCoordinator({ container: container as never, reload })
  coordinator.observe({ waiting, addEventListener: vi.fn() } as never)

  coordinator.applyUpdate()
  coordinator.applyUpdate()
  expect(waiting.postMessage).toHaveBeenCalledTimes(1)
  expect(waiting.postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' })
  expect(reload).not.toHaveBeenCalled()

  controllerChange()
  controllerChange()
  expect(reload).toHaveBeenCalledTimes(1)
})

it('detects an installed worker from updatefound and can dismiss the notice', () => {
  const installing = worker('installing')
  let updateFound!: () => void
  const registration = {
    waiting: null,
    installing,
    addEventListener: vi.fn((_name: string, listener: () => void) => { updateFound = listener }),
  }
  const coordinator = createServiceWorkerUpdateCoordinator({
    container: { controller: {}, addEventListener: vi.fn() } as never,
  })
  coordinator.observe(registration as never)
  updateFound()
  installing.state = 'installed'
  installing.dispatch('statechange')

  expect(coordinator.updateAvailable.value).toBe(true)
  coordinator.dismissUpdate()
  expect(coordinator.updateAvailable.value).toBe(false)
})

it('does not announce the initial installation as an update', () => {
  const installing = worker('installing')
  let updateFound!: () => void
  const coordinator = createServiceWorkerUpdateCoordinator({
    container: { controller: null, addEventListener: vi.fn() } as never,
  })
  coordinator.observe({
    waiting: null,
    installing,
    addEventListener: vi.fn((_name: string, listener: () => void) => { updateFound = listener }),
  } as never)

  updateFound()
  installing.state = 'installed'
  installing.dispatch('statechange')
  expect(coordinator.updateAvailable.value).toBe(false)
})
