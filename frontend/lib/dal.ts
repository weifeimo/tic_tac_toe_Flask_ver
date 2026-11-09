import 'server-only'

import { cache } from 'react'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { decrypt } from '@/lib/session'
import { db } from '@/lib/db/db'
import { sessions } from '@/lib/db/schema'
import { eq, gt } from 'drizzle-orm'


export const verifySession = cache(async () => {
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  if (!session?.sessionId) {
    redirect('/login')
  }

  const data = await db
    .select({
      userId: sessions.userId,
    })
    .from(sessions)
    .where(
      eq(sessions.id, session.sessionId)
    )

  if (data.length === 0) {
    redirect('/login')
  }

  return {
    isAuth: true,
    userId: data[0].userId,
  }
})