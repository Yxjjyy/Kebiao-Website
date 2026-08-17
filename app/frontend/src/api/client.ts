import axios, { AxiosError, AxiosHeaders, type AxiosAdapter, type AxiosInstance } from 'axios'
import { createRequestId } from './requestId'
import { getSessionToken, setSessionToken } from '@/lib/session'

declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    requestId?: string
    retryCount?: number
  }
}

interface ClientOptions {
  adapter?: AxiosAdapter
  requestId?: () => string
  sleep?: (delay: number) => Promise<void>
}

const retryableStatuses = new Set([502, 503, 504])

function canRetry(error: AxiosError): boolean {
  const config = error.config
  if (config?.method?.toLowerCase() !== 'get' || error.code === 'ERR_CANCELED') return false
  if (!error.response) return true
  return retryableStatuses.has(error.response.status)
}

function redirectToLogin() {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export function createApiClient(options: ClientOptions = {}): AxiosInstance {
  const nextRequestId = options.requestId ?? createRequestId
  const sleep = options.sleep ?? ((delay: number) => new Promise(resolve => setTimeout(resolve, delay)))
  const client = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
    ...(options.adapter ? { adapter: options.adapter } : {}),
  })

  client.interceptors.request.use((config) => {
    config.requestId ||= nextRequestId()
    config.headers = AxiosHeaders.from(config.headers)
    config.headers.set('X-Request-ID', config.requestId)
    const token = getSessionToken()
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`)
    }
    return config
  })

  client.interceptors.response.use(undefined, async (error: unknown) => {
    if (error instanceof AxiosError && error.response?.status === 401) {
      const url = error.config?.url ?? ''
      if (!url.includes('/auth/login')) {
        setSessionToken(null)
        redirectToLogin()
      }
      return Promise.reject(error)
    }
    if (!(error instanceof AxiosError) || !error.config || !canRetry(error)) {
      return Promise.reject(error)
    }
    const retryCount = error.config.retryCount ?? 0
    if (retryCount >= 2) return Promise.reject(error)

    error.config.retryCount = retryCount + 1
    await sleep(150 * error.config.retryCount)
    return client.request(error.config)
  })

  return client
}

export const api = createApiClient()
