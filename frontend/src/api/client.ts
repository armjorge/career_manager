import { getIdToken } from '@/auth/cognito'
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

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
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

async function authHeader(): Promise<Record<string, string>> {
  if (isMockMode) return {}
  const token = await getIdToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options
  const auth = await authHeader()

  const response = await fetch(`${baseUrl}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...auth,
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

export async function apiClientFormData<T>(
  path: string,
  formData: FormData,
  method = 'POST',
): Promise<T> {
  const auth = await authHeader()

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      ...auth,
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
