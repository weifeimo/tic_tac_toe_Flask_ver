import Link from 'next/link'
import SignupForm from '@/ui/signup-form'

export default function SignupPage() {
  return (
    <main>
      <h1>Sign Up</h1>
      <SignupForm />
      <p>
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </main>
  )
}