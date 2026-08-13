export type CacheStrategy = 'network-only' | 'cache-first' | 'network-first'

export interface RequestLike {
  url: string
  mode: string
  destination: string
}

const hashedAsset = /\/assets\/[^/]+-[A-Za-z0-9_-]{4,}\.(?:js|css)$/

export function classifyRequest(request: RequestLike, origin = window.location.origin): CacheStrategy {
  const url = new URL(request.url, origin)
  if (url.origin === origin && url.pathname.startsWith('/api/')) return 'network-only'
  if (url.origin === origin && hashedAsset.test(url.pathname)) return 'cache-first'
  return 'network-first'
}
