import { readonly, ref, type Ref } from 'vue'

interface CoordinatorOptions {
  container?: ServiceWorkerContainer
  reload?: () => void
}

export interface ServiceWorkerUpdateCoordinator {
  updateAvailable: Readonly<Ref<boolean>>
  observe: (registration: ServiceWorkerRegistration) => void
  applyUpdate: () => void
  dismissUpdate: () => void
}

export function createServiceWorkerUpdateCoordinator(
  options: CoordinatorOptions = {},
): ServiceWorkerUpdateCoordinator {
  const updateAvailable = ref(false)
  let waitingWorker: ServiceWorker | null = null
  let activationRequested = false
  let reloaded = false
  const container = options.container
    ?? (typeof navigator !== 'undefined' ? navigator.serviceWorker : undefined)
  const reload = options.reload
    ?? (() => window.location.reload())

  container?.addEventListener('controllerchange', () => {
    if (!activationRequested || reloaded) return
    reloaded = true
    reload()
  })

  function markWaiting(worker: ServiceWorker | null | undefined) {
    if (!worker) return
    waitingWorker = worker
    updateAvailable.value = true
  }

  function observe(registration: ServiceWorkerRegistration) {
    markWaiting(registration.waiting)
    registration.addEventListener('updatefound', () => {
      const installing = registration.installing
      if (!installing) return
      installing.addEventListener('statechange', () => {
        if (installing.state === 'installed' && container?.controller) {
          markWaiting(registration.waiting ?? installing)
        }
      })
    })
  }

  function applyUpdate() {
    if (!waitingWorker || activationRequested) return
    activationRequested = true
    waitingWorker.postMessage({ type: 'SKIP_WAITING' })
  }

  function dismissUpdate() {
    updateAvailable.value = false
  }

  return { updateAvailable: readonly(updateAvailable), observe, applyUpdate, dismissUpdate }
}

const coordinator = createServiceWorkerUpdateCoordinator()

export function useServiceWorkerUpdate() {
  return coordinator
}
