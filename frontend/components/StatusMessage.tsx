// frontend/components/StatusMessage.tsx
import type { GameState } from "@/types/game";
import styles from "./game.module.css";

type Props = {
  game: GameState | null;
  loading: boolean;
  error: string | null;
};

const markOf = (player: 0 | 1) => (player === 0 ? "X" : "O");

/** メッセージ表示（元の h3#message に相当） */
export default function StatusMessage({ game, loading, error }: Props) {
  let message = "";
  let finished = false; // 勝利・引き分け時は赤背景にする

  if (error) {
    // 通信エラーのときはエラーメッセージを表示する（元の実装と同じ）
    message = error;
  } else if (!game) {
    message = loading ? "Loading..." : "";
  } else if (game.status === "win" && game.winner !== null) {
    message = `${markOf(game.winner)} Wins!`;
    finished = true;
  } else if (game.status === "draw") {
    message = "Draw!";
    finished = true;
  } else {
    // 注意: ゲーム終了後は player が切り替わらないため、勝者は winner を使う
    message = `${markOf(game.player)} 's Turn`;
  }

  return (
    <h3
      className={`${styles.message} ${finished ? styles.winnerMessage : ""}`}
      role={error ? "alert" : undefined}
    >
      {message}
    </h3>
  );
}