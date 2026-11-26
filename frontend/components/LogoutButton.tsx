// frontend/components/LogoutButton.tsx
'use client'

import { useActionState } from "react";
import { logout } from "@/app/actions/auth";
import styles from "./game.module.css";

/** ログアウトボタン。logout アクション（DBのセッション削除 → Cookie削除 → /login へ）を呼ぶ。
 *  DB削除に失敗した場合は Cookie が残ったままエラーが返るので、メッセージを表示して再試行できるようにする */
export default function LogoutButton() {
  const [state, formAction, pending] = useActionState(logout, undefined);

  return (
    <form action={formAction} className={styles.logoutForm}>
      <button type="submit" className={styles.BarButton} disabled={pending}>
        {pending ? "LOGGING OUT..." : "LOG OUT"}
      </button>
      {state?.message && <p role="alert">{state.message}</p>}
    </form>
  );
}