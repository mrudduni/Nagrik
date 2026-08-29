// ---------------------------------------------------------------------------
// Fake network client shared by every service module.
//
// Every service function in src/services is written as if it were calling a
// real FastAPI backend: it's async, it can fail, and it goes through this one
// choke point. Today `request()` just resolves mock data after a simulated
// delay. When the backend exists, only this file (and each service's data
// source) needs to change - components and pages never talk to mock data
// directly.
// ---------------------------------------------------------------------------

const SIMULATED_LATENCY_MS = 380

export function delay<T>(value: T, ms: number = SIMULATED_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export async function request<T>(factory: () => T, ms: number = SIMULATED_LATENCY_MS): Promise<T> {
  await delay(null, ms)
  return factory()
}

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string = "unknown_error",
  ) {
    super(message)
    this.name = "ApiError"
  }
}
