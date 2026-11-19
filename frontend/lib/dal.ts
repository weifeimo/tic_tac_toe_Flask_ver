import 'server-only'

import { cache } from 'react'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { and, eq, gt } from 'drizzle-orm'
import { decrypt } from '@/lib/session'
import { db } from '@/lib/db/db'
import { sessions, users } from '@/lib/db/schema'

// DB から session をチェックする。無効の場合は null を返し、redirect はしない
export const getSession = cache(async () => {
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  if (typeof session?.sessionId !== 'string') return null

  const [row] = await db
    .select({ userId: sessions.userId })
    .from(sessions)
    .where(
      and(
        eq(sessions.id, session.sessionId),
        gt(sessions.expiresAt, new Date())
      )
    )
    .limit(1)

  return row ? { isAuth: true as const, userId: row.userId } : null
})

export const verifySession = cache(async () => {
  const session = await getSession()
  if (!session) redirect('/login')
  return session
})

// ログイン中のユーザー情報を取得する（password は取得しない）
export const getUser = cache(async () => {
  const session = await verifySession()

  const [user] = await db
    .select({ id: users.id, username: users.username })
    .from(users)
    .where(eq(users.id, session.userId))
    .limit(1)

  if (!user) {
    redirect('/login')
  }

  return user
})