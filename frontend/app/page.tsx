// frontend/app/page.tsx
"use client"; // useState / useEffect を使うため、クライアントコンポーネントにする

import { useCallback, useEffect, useState } from "react";
import Board from "@/components/Board";
import RestartButton from "@/components/RestartButton";
import StatusMessage from "@/components/StatusMessage";
import styles from "@/components/game.module.css";
import { ApiError, getState, play, startGame } from "@/lib/api";
import type { GameState } from "@/types/game";

export default function Home() {
  const [game, setGame] = useState<GameState | null>(null); // サーバーから取得したゲーム状態
  const [loading, setLoading] = useState(true);              // 通信中かどうか
  const [error, setError] = useState<string | null>(null);   // エラーメッセージ

  /**
   * API 呼び出しの共通処理。
   * 通信中フラグとエラーを管理し、成功したら画面の状態を更新する。
   */
  const run = useCallback(async (action: () => Promise<GameState>) => {
    setLoading(true);
    setError(null);
    try {
      setGame(await action());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "不明なエラーが発生しました。");
    } finally {
      setLoading(false);
    }
  }, []);

  // 初回表示時（ページの再読み込み時も）に現在のゲーム状態を取得して復元する
  useEffect(() => {
    run(getState);
  }, [run]);

  const handleCellClick = (index: number) => run(() => play(index));
  const handleRestart = () => run(startGame);

  // 盤面を操作できない条件：通信中・状態未取得・ゲーム終了
  const boardDisabled = loading || !game || !game.game_running;

  // RESTART ボタンは、ゲーム終了後だけ表示する（元の実装と同じ）
  // 初回取得に失敗して盤面がない場合も、やり直せるように表示する
  const showRestart = game ? !game.game_running : error !== null;

  return (
    <main>
      <h2 className={styles.title}>TIC TAC TOE</h2>

      <StatusMessage game={game} loading={loading} error={error} />

      {game && (
        <Board
          cells={game.cells}
          winningPattern={game.winning_pattern}
          disabled={boardDisabled}
          onCellClick={handleCellClick}
        />
      )}

      {showRestart && <RestartButton disabled={loading} onClick={handleRestart} />}
    </main>
  );
}