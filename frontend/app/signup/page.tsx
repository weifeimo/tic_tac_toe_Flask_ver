import Link from 'next/link'
import SignupForm from '@/ui/signup-form'
import styles from "@/components/game.module.css";

export default function SignupPage() {
  return (
    <main>
      <div className={styles.userBar}>
        <span className={styles.textdefault}>Already have an account? </span>
        <Link href="/login" className={styles.BarButton}>
          Log in
        </Link>
      </div>

      <h2 className={styles.signupTitle}>Sign Up</h2>
      <SignupForm />

    </main>
  )
}