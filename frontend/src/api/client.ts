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
    return (await response.json()) as ApiError
  } catch {
    return { message: response.statusText || 'Request failed' }
  }
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
