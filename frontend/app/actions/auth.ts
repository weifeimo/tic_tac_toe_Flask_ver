'use server'

import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto'
import { promisify } from 'node:util'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { eq } from 'drizzle-orm'
import * as z from 'zod'

import { db } from '@/lib/db/db'
import { sessions, users } from '@/lib/db/schema'
import { SignupFormSchema, FormState } from '@/lib/definitions'
import { createSession, decrypt, deleteSession } from '@/lib/session'

const scrypt = promisify(scryptCallback)

// ログイン/登録後の遷移先（proxy.ts の保護ルートと合わせて調整してください）
const AFTER_AUTH_PATH = '/'
const LOGIN_PATH = '/login'

const KEY_LENGTH = 64

// ログイン用のスキーマ。
// 登録時のパスワードは SignupFormSchema 側で .trim() されてからハッシュ化されるため、
// ログイン時も同じ前処理（trim）をしないと照合が一致しなくなる。
const LoginFormSchema = z.object({
  name: z.string().trim().min(1, { error: 'Please enter your username.' }),
  password: z.string().min(1, { error: 'Please enter your password.' }),
})

// ---------------------------------------------------------------------------
// パスワードハッシュ（Node 標準の scrypt を使用。追加パッケージ不要）
// 保存形式: "<salt hex>:<hash hex>"
// ---------------------------------------------------------------------------
async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16)
  const hash = (await scrypt(password, salt, KEY_LENGTH)) as Buffer
  return `${salt.toString('hex')}:${hash.toString('hex')}`
}

async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [saltHex, hashHex] = stored.split(':')
  if (!saltHex || !hashHex) return false

  const expected = Buffer.from(hashHex, 'hex')
  const actual = (await scrypt(password, Buffer.from(saltHex, 'hex'), expected.length)) as Buffer

  return actual.length === expected.length && timingSafeEqual(actual, expected)
}

// Postgres の一意制約違反（23505）。Drizzle のバージョンによりエラーが cause に包まれるため両方確認する
function isUniqueViolation(error: unknown): boolean {
  const e = error as { code?: string; cause?: { code?: string } } | null
  return e?.code === '23505' || e?.cause?.code === '23505'
}

// ---------------------------------------------------------------------------
// 新規登録
// ---------------------------------------------------------------------------
export async function signup(state: FormState, formData: FormData): Promise<FormState> {
  // 1. 入力チェック
  const validatedFields = SignupFormSchema.safeParse({
    name: formData.get('name'),
    password: formData.get('password'),
  })

  if (!validatedFields.success) {
    return { errors: z.flattenError(validatedFields.error).fieldErrors }
  }

  const { name, password } = validatedFields.data

  // 2. ユーザーを作成（username は DB 側で unique）
  let userId: number
  try {
    const [user] = await db
      .insert(users)
      .values({
        username: name,
        password: await hashPassword(password),
      })
      .returning({ id: users.id })

    userId = user.id
  } catch (error) {
    if (isUniqueViolation(error)) {
      return { errors: { name: ['This username is already taken.'] } }
    }
    console.error('signup failed:', error)
    return { message: 'Something went wrong. Please try again.' }
  }

  // 3. セッション作成 → 4. リダイレクト
  // redirect() は内部で例外を投げるので、try/catch の外で呼ぶこと
  await createSession(userId)
  redirect(AFTER_AUTH_PATH)
}

// ---------------------------------------------------------------------------
// ログイン
// ---------------------------------------------------------------------------
export async function login(state: FormState, formData: FormData): Promise<FormState> {
  const validatedFields = LoginFormSchema.safeParse({
    name: formData.get('name'),
    password: formData.get('password'),
  })

  if (!validatedFields.success) {
    return { errors: z.flattenError(validatedFields.error).fieldErrors }
  }

  const { name, password } = validatedFields.data

  // ユーザーが存在するかどうかを漏らさないため、エラーメッセージは常に同じにする
  const invalidCredentials: FormState = { message: 'Invalid username or password.' }

  let userId: number
  try {
    const [user] = await db
      .select({ id: users.id, password: users.password })
      .from(users)
      .where(eq(users.username, name))
      .limit(1)

    if (!user) {
      // ユーザーが存在しない場合も同程度の時間をかけて、応答時間の差から推測されないようにする
      await hashPassword(password)
      return invalidCredentials
    }

    if (!(await verifyPassword(password, user.password))) {
      return invalidCredentials
    }

    userId = user.id
  } catch (error) {
    console.error('login failed:', error)
    return { message: 'Something went wrong. Please try again.' }
  }

  await createSession(userId)
  redirect(AFTER_AUTH_PATH)
}

// ---------------------------------------------------------------------------
// ログアウト
// DB のセッション行を削除できた場合のみ Cookie を消してログアウト完了とする。
// 削除に失敗した場合は Cookie を残したままエラーを返し、再試行できるようにする。
// ---------------------------------------------------------------------------
export type LogoutState = { message?: string } | undefined

async function deleteSessionRow(sessionId: string): Promise<void> {
  const MAX_ATTEMPTS = 2 // 一時的な DB エラーに備えて 1 回だけ再試行
  for (let attempt = 1; ; attempt++) {
    try {
      await db.delete(sessions).where(eq(sessions.id, sessionId))
      return
    } catch (error) {
      if (attempt >= MAX_ATTEMPTS) throw error
    }
  }
}

export async function logout(_state: LogoutState): Promise<LogoutState> {
  const token = (await cookies()).get('session')?.value
  const payload = await decrypt(token)

  // Cookie が無い/不正な場合は DB 側に消すものが無いので、そのまま Cookie 削除へ進む
  if (typeof payload?.sessionId === 'string') {
    try {
      await deleteSessionRow(payload.sessionId)
    } catch (error) {
      console.error('failed to delete session row:', error)
      // Cookie は削除せず、ログアウト成功として扱わない
      return { message: 'ログアウトに失敗しました。もう一度お試しください。' }
    }
  }

  await deleteSession()
  redirect(LOGIN_PATH) // redirect() は例外を投げるので try/catch の外
}