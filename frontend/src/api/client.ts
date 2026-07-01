import { getStoredToken } from '@/auth/tokenStorage'
import type { ApiError } from '@/types'

export class ApiClientError extends Error {
  status: number
  code?: string

  constructor(message: string, status = 400, code?: string) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
  }
}

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'mock'
export const isMockMode = baseUrl === 'mock'

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as Record<string, unknown>
    if (typeof body.message === 'string') {
      return { message: body.message, code: typeof body.code === 'string' ? body.code : undefined }
    }
    if (typeof body.detail === 'string') {
      return { message: body.detail }
    }
    if (Array.isArray(body.detail)) {
      const first = body.detail[0] as { msg?: string } | undefined
      if (first?.msg) {
        return { message: first.msg, code: 'VALIDATION_ERROR' }
      }
    }
  } catch {
    return { message: response.statusText || 'Request failed' }
  }
  return { message: response.statusText || 'Request failed' }
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options

  const token = getStoredToken()

  const response = await fetch(`${baseUrl}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const error = await parseError(response)
    throw new ApiClientError(error.message, response.status, error.code)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function apiClientFormData<T>(path: string, formData: FormData, method = 'POST'): Promise<T> {
  const token = getStoredToken()

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await parseError(response)
    throw new ApiClientError(error.message, response.status, error.code)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
