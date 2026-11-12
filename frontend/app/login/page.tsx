import Link from 'next/link'
import LoginForm from '@/ui/login-form'
import styles from "@/components/game.module.css";

export default function LoginPage() {
  return (
    <main>
      <div className={styles.userBar}>
        <span className={styles.textDefault}>Don&apos;t have an account?</span>
        <Link href="/signup" className={styles.BarButton}>
          Sign up
        </Link>
      </div>
      <div className={styles.redline}></div>
      <h2 className={styles.loginTitle}>Log In</h2>
      <div className={styles.redline}></div>
      <div style={{ marginBottom: "36px" }}></div>
      <LoginForm />
    </main>
  )
}