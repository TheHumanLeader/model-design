let fallbackSequence = 0

export function createId(prefix: string): string {
  const uuid = globalThis.crypto?.randomUUID?.()

  if (uuid) {
    return `${prefix}_${uuid}`
  }

  fallbackSequence += 1
  return `${prefix}_${Date.now().toString(36)}_${fallbackSequence.toString(36)}_${Math.random()
    .toString(36)
    .slice(2, 8)}`
}
