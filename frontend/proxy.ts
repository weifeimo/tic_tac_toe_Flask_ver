import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'

// ゲームページ（/）ログイン必要；ログイン/サインアップページはログインしてない状態でアクセス可能
const publicRoutes = ['/login', '/signup']
const AFTER_AUTH_PATH = '/'

const encodedKey = new TextEncoder().encode(process.env.SESSION_SECRET)

// proxy では JWT の署名検証のみを行い、データベースにはアクセスしない
// （DB 内の session が有効かどうかは、lib/dal.ts の verifySession で再度確認する）
async function hasValidSession(req: NextRequest): Promise<boolean> {
  const token = req.cookies.get('session')?.value
  if (!token) return false

  try {
    const { payload } = await jwtVerify(token, encodedKey, {
      algorithms: ['HS256'],
    })
    return typeof payload.sessionId === 'string'
  } catch {
    return false
  }
}

export async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname
  const isPublicRoute = publicRoutes.includes(path)
  const isLoggedIn = await hasValidSession(req)

  // ログインしてない → ログインページ
  if (!isPublicRoute && !isLoggedIn) {
    return NextResponse.redirect(new URL('/login', req.nextUrl))
  }

  // ログイン済でログインページやサインアップページを閲覧 → ゲームページ
  if (isPublicRoute && isLoggedIn) {
    return NextResponse.redirect(new URL(AFTER_AUTH_PATH, req.nextUrl))
  }

  return NextResponse.next()
}

// proxy を実行しないパス
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|ico|webp)$).*)'],
}