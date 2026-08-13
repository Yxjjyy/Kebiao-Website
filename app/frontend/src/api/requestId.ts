export function createRequestId(
  generate: () => string = () => crypto.randomUUID(),
): string {
  return generate()
}
