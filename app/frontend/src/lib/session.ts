export const SESSION_TOKEN_KEY = 'lumina_session_token'

export function getSessionToken(): string | null {
  return localStorage.getItem(SESSION_TOKEN_KEY)
}

export function setSessionToken(token: string | null) {
  if (token) {
    localStorage.setItem(SESSION_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(SESSION_TOKEN_KEY)
  }
}
