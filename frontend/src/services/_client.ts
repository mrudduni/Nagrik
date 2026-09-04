// ---------------------------------------------------------------------------
// Real API client for the Nagrik FastAPI backend
// ---------------------------------------------------------------------------

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

const DEFAULT_TIMEOUT_MS = 90000

export function delay<T>(
  value: T,
  ms: number = 0
): Promise<T> {
  return new Promise((resolve) =>
    setTimeout(() => resolve(value), ms)
  )
}

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string = "unknown_error",
    public status?: number,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function httpsrequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController()

  const timeout = setTimeout(
    () => controller.abort(),
    timeoutMs
  )

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new ApiError(
        data?.detail ||
          data?.message ||
          `Request failed with status ${response.status}`,
        data?.code || "api_error",
        response.status,
      )
    }

    return data as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(
        "Request timed out",
        "timeout",
      )
    }

    throw new ApiError(
      error instanceof Error
        ? error.message
        : "Network request failed",
      "network_error",
    )
  } finally {
    clearTimeout(timeout)
  }
}

export async function apiGet<T>(
  endpoint: string,
): Promise<T> {
  return httpsrequest<T>(endpoint, {
    method: "GET",
  })
}

export async function apiPost<T>(
  endpoint: string,
  body?: unknown,
): Promise<T> {
  return httpsrequest<T>(endpoint, {
    method: "POST",
    body: body !== undefined
      ? JSON.stringify(body)
      : undefined,
  })
}

export async function apiPatch<T>(
  endpoint: string,
  body?: unknown,
): Promise<T> {
  return httpsrequest<T>(endpoint, {
    method: "PATCH",
    body: body !== undefined
      ? JSON.stringify(body)
      : undefined,
  })
}

export async function apiDelete<T>(
  endpoint: string,
): Promise<T> {
  return httpsrequest<T>(endpoint, {
    method: "DELETE",
  })
}

export async function request<T>(
  factory: () => T,
  ms: number = 380,
): Promise<T> {
  await delay(null, ms)
  return factory()
}

