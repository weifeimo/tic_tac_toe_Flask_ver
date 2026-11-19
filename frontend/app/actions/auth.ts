'use server'

import {
  randomBytes,
  scrypt as scryptCallback,
  timingSafeEqual,
  type ScryptOptions,
} from 'node:crypto'
import { promisify } from 'node:util'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { eq } from 'drizzle-orm'
import * as z from 'zod'

import { db } from '@/lib/db/db'
import { sessions, users } from '@/lib/db/schema'
import { SignupFormSchema, FormState } from '@/lib/definitions'
import { createSession, decrypt, deleteSession } from '@/lib/session'

// promisify(scrypt) は @types/node のバージョンによって options 付きの
// オーバーロードが推論されない（引数 3 つ扱いになる）ため、型を明示する。
// options を省略した場合は Node.js のデフォルトパラメータで動作する（旧形式の検証で使用）。
const scrypt = promisify(scryptCallback) as (
  password: string,
  salt: Buffer,
  keylen: number,
  options?: ScryptOptions,
) => Promise<Buffer>

// ログイン/登録後の遷移先（proxy.ts の保護ルートと合わせて調整してください）
const AFTER_AUTH_PATH = '/'
const LOGIN_PATH = '/login'

const KEY_LENGTH = 64

// scrypt のパラメータ（OWASP Password Storage Cheat Sheet を参考）
// バージョンごとにパラメータを定義しておくことで、将来パラメータを変更しても
// 既存のハッシュを検証でき、ログイン成功時に最新バージョンへ移行できる。
// 一度公開したバージョンのパラメータは変更しないこと（新しいバージョンを追加する）。
const SCRYPT_PARAMS_BY_VERSION = {
  v1: {
    N: 2 ** 17,
    r: 8,
    p: 1,
    maxmem: 256 * 1024 * 1024,
  },
} as const

type ScryptVersion = keyof typeof SCRYPT_PARAMS_BY_VERSION
const CURRENT_VERSION: ScryptVersion = 'v1'

// 旧形式のパスワードハッシュとの互換性を維持するための設定
// 旧形式は Node.js のデフォルトパラメータで生成されている
const LEGACY_KEY_LENGTH = 64

// ログイン用のスキーマ。
// 登録時のパスワードは SignupFormSchema 側で .trim() されてからハッシュ化されるため、
// ログイン時も同じ前処理（trim）をしないと照合が一致しなくなる。
const LoginFormSchema = z.object({
  name: z.string().trim().min(1, { error: 'Please enter your username.' }),
  password: z.string().min(1, { error: 'Please enter your password.' }),
})

// ---------------------------------------------------------------------------
// パスワードハッシュ
// 保存形式: "scrypt$<version>$<salt hex>$<hash hex>"
// version は SCRYPT_PARAMS_BY_VERSION のパラメータセットに対応する
// ---------------------------------------------------------------------------
async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16)

  const hash = await scrypt(
    password,
    salt,
    KEY_LENGTH,
    SCRYPT_PARAMS_BY_VERSION[CURRENT_VERSION],
  )

  return `scrypt$${CURRENT_VERSION}$${salt.toString('hex')}$${hash.toString('hex')}`
}

type VerifyResult = { valid: boolean; needsRehash: boolean }
const INVALID: VerifyResult = { valid: false, needsRehash: false }

// 検証結果に加えて、保存されているハッシュを最新のパラメータで
// 作り直すべきか（needsRehash）も返す。
async function verifyPassword(password: string, stored: string): Promise<VerifyResult> {
  const parts = stored.split('$')

  let salt: Buffer
  let expected: Buffer
  let actual: Buffer
  let needsRehash: boolean

  // 新形式: アルゴリズムとパラメータバージョンを確認する
  if (parts.length === 4 && parts[0] === 'scrypt') {
    const [, version, saltHex, hashHex] = parts

    // 未知のバージョンは拒否（DB の値から任意のパラメータを読み込まない）
    if (!Object.hasOwn(SCRYPT_PARAMS_BY_VERSION, version)) return INVALID
    const options = SCRYPT_PARAMS_BY_VERSION[version as ScryptVersion]

    if (!/^[0-9a-f]+$/i.test(saltHex) || !/^[0-9a-f]+$/i.test(hashHex)) {
      return INVALID
    }

    salt = Buffer.from(saltHex, 'hex')
    expected = Buffer.from(hashHex, 'hex')

    if (salt.length !== 16 || expected.length !== KEY_LENGTH) return INVALID

    actual = await scrypt(password, salt, expected.length, options)

    // 古いバージョンのハッシュは、ログイン成功後に最新バージョンへ移行する
    needsRehash = version !== CURRENT_VERSION

  // 旧形式: "<salt hex>:<hash hex>"
  // 既存ユーザーのパスワードを引き続き検証できるようにする
  } else if (parts.length === 1 && stored.includes(':')) {
    const [saltHex, hashHex] = stored.split(':')

    if (
      !saltHex ||
      !hashHex ||
      !/^[0-9a-f]+$/i.test(saltHex) ||
      !/^[0-9a-f]+$/i.test(hashHex)
    ) {
      return INVALID
    }

    salt = Buffer.from(saltHex, 'hex')
    expected = Buffer.from(hashHex, 'hex')

    if (salt.length !== 16 || expected.length !== LEGACY_KEY_LENGTH) {
      return INVALID
    }

    // 旧形式は変更前の Node.js デフォルトパラメータで検証する
    actual = await scrypt(password, salt, expected.length)

    // 旧形式は一律で新形式へ移行する
    needsRehash = true
  } else {
    return INVALID
  }

  const valid = actual.length === expected.length && timingSafeEqual(actual, expected)
  return { valid, needsRehash: valid && needsRehash }
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

    const result = await verifyPassword(password, user.password)
    if (!result.valid) {
      return invalidCredentials
    }

    // 旧形式 / 旧バージョンのハッシュは、ログイン成功後に最新のパラメータへ移行する。
    // 移行に失敗してもログイン自体は成功させる。
    if (result.needsRehash) {
      try {
        await db
          .update(users)
          .set({ password: await hashPassword(password) })
          .where(eq(users.id, user.id))
      } catch (error) {
        console.error('password rehash failed:', error)
      }
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