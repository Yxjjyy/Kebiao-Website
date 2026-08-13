import { describe, expect, it } from 'vitest'
import { classifyRequest } from './serviceWorkerPolicy'

describe('service worker request policy', () => {
  it.each([
    ['https://app.test/api/v1/lessons', 'same-origin', 'navigate', 'network-only'],
    ['https://app.test/assets/index-Ab12_3.js', 'same-origin', 'script', 'cache-first'],
    ['https://app.test/assets/index-a1b2.css', 'same-origin', 'style', 'cache-first'],
    ['https://app.test/students', 'same-origin', 'navigate', 'network-first'],
    ['https://app.test/favicon.svg', 'same-origin', 'image', 'network-first'],
  ] as const)('classifies %s as %s', (url, _origin, destination, expected) => {
    expect(classifyRequest({ url, mode: destination === 'navigate' ? 'navigate' : 'cors', destination }, 'https://app.test')).toBe(expected)
  })
})
