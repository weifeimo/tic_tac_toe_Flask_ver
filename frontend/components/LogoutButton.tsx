// frontend/components/LogoutButton.tsx
import { logout } from "@/app/actions/auth";
import styles from "./game.module.css";

/** ログアウトボタン。logout アクション（DBのセッション削除 → Cookie削除 → /login へ）を呼ぶ */
export default function LogoutButton() {
  return (
    <form action={logout} className={styles.logoutForm}>
      <button type="submit" className={styles.BarButton}>
        LOG OUT
      </button>
    </form>
  );
}