const CACHE_KEY = 'kebiao-static-v2'
const PRECACHE = ['/offline.html', '/manifest.json', '/favicon.svg']
const HASHED_ASSET = /\/assets\/[^/]+-[A-Za-z0-9_-]{4,}\.(?:js|css)$/

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_KEY).then((cache) => cache.addAll(PRECACHE)))
})

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_KEY).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  )
})

async function cacheFirst(request) {
  const cached = await caches.match(request)
  if (cached) return cached
  const response = await fetch(request)
  if (response.ok) {
    const cache = await caches.open(CACHE_KEY)
    await cache.put(request, response.clone())
  }
  return response
}

async function networkFirst(request) {
  try {
    const response = await fetch(request)
    if (response.ok && new URL(request.url).origin === self.location.origin) {
      const cache = await caches.open(CACHE_KEY)
      await cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    if (request.mode === 'navigate') return caches.match('/offline.html')
    const cached = await caches.match(request)
    if (cached) return cached
    throw error
  }
}

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return
  const url = new URL(event.request.url)
  if (url.origin === self.location.origin && url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request))
    return
  }
  event.respondWith(HASHED_ASSET.test(url.pathname)
    ? cacheFirst(event.request)
    : networkFirst(event.request))
})
