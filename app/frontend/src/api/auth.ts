import { api } from './client'

export interface LoginResult {
  token: string
}

export const authApi = {
  login: (username: string, password: string) =>
    api
      .post<LoginResult>('/auth/login', { username, password })
      .then((r) => r.data),

  logout: () => api.post<{ ok: boolean }>('/auth/logout').then((r) => r.data),

  me: () => api.get<{ ok: boolean }>('/auth/me').then((r) => r.data),
}
