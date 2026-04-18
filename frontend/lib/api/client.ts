import { ApiError } from './schemas'

const DEFAULT_TIMEOUT_MS = 60_000

function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL
  if (!url) {
    throw new ApiError(0, 'NEXT_PUBLIC_API_BASE_URL 未配置，无法连接后端')
  }
  return url.replace(/\/$/, '')
}

function extractDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback
  const obj = body as Record<string, unknown>
  const detail = obj.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as Record<string, unknown>
    const msg = first?.msg
    if (typeof msg === 'string') return msg
  }
  return fallback
}

export async function postJson<TReq, TRes>(
  path: string,
  body: TReq,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<TRes> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  const url = `${getBaseUrl()}${path}`

  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    if ((err as Error).name === 'AbortError') {
      throw new ApiError(0, '请求超时，请稍后重试')
    }
    throw new ApiError(0, `网络错误：${(err as Error).message}`)
  }
  clearTimeout(timer)

  const text = await response.text()
  let parsed: unknown = undefined
  if (text) {
    try {
      parsed = JSON.parse(text)
    } catch {
      parsed = undefined
    }
  }

  if (!response.ok) {
    const detail = extractDetail(parsed, `请求失败 (${response.status})`)
    throw new ApiError(response.status, detail)
  }

  return parsed as TRes
}

export async function getJson<TRes>(path: string, timeoutMs: number = 10_000): Promise<TRes> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  const url = `${getBaseUrl()}${path}`

  let response: Response
  try {
    response = await fetch(url, { signal: controller.signal })
  } catch (err) {
    clearTimeout(timer)
    if ((err as Error).name === 'AbortError') {
      throw new ApiError(0, '请求超时，请稍后重试')
    }
    throw new ApiError(0, `网络错误：${(err as Error).message}`)
  }
  clearTimeout(timer)

  const text = await response.text()
  const parsed = text ? JSON.parse(text) : undefined

  if (!response.ok) {
    throw new ApiError(response.status, extractDetail(parsed, `请求失败 (${response.status})`))
  }
  return parsed as TRes
}
