// frontend/app/page.tsx
import Game from "@/components/Game";
import LogoutButton from "@/components/LogoutButton";
import styles from "@/components/game.module.css";
import { getUser } from "@/lib/dal";

export default async function Home() {
  const user = await getUser();

  return (
    <main>
      <div className={styles.userBar}>
        <span className={styles.welcome}>Welcome, {user.username}</span>
        <LogoutButton />
      </div>

      <Game />
    </main>
  );
}