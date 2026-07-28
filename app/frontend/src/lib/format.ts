export function formatCurrency(value: number, symbol = '¥') {
  return `${symbol}${value.toFixed(0)}`
}

export function formatHours(value: number) {
  return `${Number(value.toFixed(1))}h`
}

export function formatPercent(value: number | null) {
  if (value === null) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}
