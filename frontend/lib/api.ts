// frontend/lib/api.ts
import type { GameState } from "@/types/game";

/**
 * API 通信の失敗を表すエラー。
 * status: HTTP ステータスコード（ネットワーク障害など、レスポンスがない場合は null）
 */
export class ApiError extends Error {
/**                   JS の Error から継承 */
  status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * 共通のリクエスト処理。
 * - /api/... は next.config.ts の rewrites で Flask に転送される（同一オリジンなので cookie も送られる）
 * - 通信失敗・HTTP エラー・JSON 解析エラーをすべて ApiError にまとめる
 * 対応する内容：
 * getState()       // GET /api/state（読み取り専用。ゲームがなければ null）
 * startGame()      // POST /api/start（新しいゲームを作成）
 * play(position)   // POST /api/play/<position>
 */
async function request(path: string, init?: RequestInit): Promise<GameState> {
  let response: Response;

  try {
    response = await fetch(path, {
      ...init,
      credentials: "same-origin", // Flask の session cookie を送受信する
      cache: "no-store",          // 常に最新のゲーム状態を取得する
    });
  } catch {
    // サーバーに到達できない場合（Flask が停止している、ネットワーク切断など）
    throw new ApiError("サーバーに接続できませんでした。通信状態を確認してください。");
  }

  if (!response.ok) {
    // 期待値：200-299。404、500などを排除
    throw new ApiError(
      `サーバーエラーが発生しました（${response.status}）。`,
      response.status,
    );
  }

  try {
    return (await response.json()) as GameState;
  } catch {
    throw new ApiError("サーバーの応答を読み取れませんでした。", response.status);
  }
}

/**
 * 現在のゲーム状態を取得する（GET /api/state）。読み取り専用で、ゲームは作成されない。
 * まだゲームがない場合（サーバーが 404 を返す）は null を返す。
 */
export async function getState(): Promise<GameState | null> {
  try {
    return await request("/api/state");
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return null;
    }
    throw e;
  }
}

/** 新しいゲームを開始する（POST /api/start） */
export function startGame(): Promise<GameState> {
  return request("/api/start", { method: "POST" });
}

/** 指定したマス（0〜8）に打つ（POST /api/play/<position>） */
export function play(position: number): Promise<GameState> {
  return request(`/api/play/${position}`, { method: "POST" });
}