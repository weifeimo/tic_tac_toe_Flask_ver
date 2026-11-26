import Link from 'next/link'
import { redirect } from 'next/navigation'
import LoginForm from '@/ui/login-form'
import { getSession } from '@/lib/dal'
import styles from "@/components/game.module.css";

export default async function LoginPage() {
  // DB内の session が有効時のみ redirect する（JWT 有效が DB 無効の場合、LoginForm を表示する）
  if (await getSession()) redirect('/')
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