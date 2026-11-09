import 'server-only'
import { SignJWT, jwtVerify } from 'jose'
import { cookies } from 'next/headers'
import { eq } from 'drizzle-orm'
import { db } from '@/lib/db/db'
import { sessions } from '@/lib/db/schema'
import { SessionPayload } from '@/lib/definitions'

const secretKey = process.env.SESSION_SECRET
if (!secretKey) {
  throw new Error('SESSION_SECRET is not defined')
}
const encodedKey = new TextEncoder().encode(secretKey)

const COOKIE_NAME = 'session'
const SESSION_DURATION_MS = 7 * 24 * 60 * 60 * 1000

function cookieOptions(expiresAt: Date) {
  return {
    httpOnly: true,
    // 本番環境のみ secure（http の localhost でも動かすため）
    secure: process.env.NODE_ENV === 'production',
    expires: expiresAt,
    sameSite: 'lax' as const,
    path: '/',
  }
}

export async function encrypt(payload: SessionPayload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(encodedKey)
}

export async function decrypt(session: string | undefined = '') {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ['HS256'],
    })
    return payload
  } catch {
    return undefined
  }
}

// ログイン状態の作成（DBにセッションを作成し、CookieにJWTを保存する）
export async function createSession(userId: number) {
  const expiresAt = new Date(Date.now() + SESSION_DURATION_MS)

  const [row] = await db
    .insert(sessions)
    .values({ userId, expiresAt })
    .returning({ id: sessions.id })

  const session = await encrypt({ sessionId: row.id, expiresAt })

  const cookieStore = await cookies()
  cookieStore.set(COOKIE_NAME, session, cookieOptions(expiresAt))
}

// ログイン状態の延長（DB と Cookie の両方の有効期限を延ばす）
// 注意: Cookie の書き込みは Server Action / Route Handler の中でのみ可能
export async function updateSession() {
  const cookieStore = await cookies()
  const session = cookieStore.get(COOKIE_NAME)?.value
  const payload = await decrypt(session)

  if (!session || typeof payload?.sessionId !== 'string') {
    return null
  }

  const expiresAt = new Date(Date.now() + SESSION_DURATION_MS)

  await db
    .update(sessions)
    .set({ expiresAt })
    .where(eq(sessions.id, payload.sessionId))

  const newSession = await encrypt({ sessionId: payload.sessionId, expiresAt })
  cookieStore.set(COOKIE_NAME, newSession, cookieOptions(expiresAt))
}

// ログアウト用（Cookie の削除のみ。DB 側の削除は logout アクションで行う）
export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete(COOKIE_NAME)
}