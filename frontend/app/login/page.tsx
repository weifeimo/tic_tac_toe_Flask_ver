import Link from 'next/link'
import LoginForm from '@/ui/login-form'

export default function LoginPage() {
  return (
    <main>
      <h1>Log In</h1>
      <LoginForm />
      <p>
        Don&apos;t have an account? <Link href="/signup">Sign up</Link>
      </p>
    </main>
  )
}