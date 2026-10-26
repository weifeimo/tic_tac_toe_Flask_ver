// frontend/types/game.ts

/** プレイヤー：0 = X，1 = O */
export type Player = 0 | 1;

/** Cell:プレイヤーのSymbolか、null */
export type Cell = Player | null;

/** GameStatus："playing" 対戦中 / "win" 勝者あり / "draw" 引き分け */
export type GameStatus = "playing" | "win" | "draw";

/** Flask の /api/state、/api/start、/api/play/<position> が返す JSON */
export type GameState = {
  game_id: string;
  cells: Cell[];                    // length = 9，0〜8 の順番で左上から右下まで
  player: Player;                   // 誰の番
  game_running: boolean;
  status: GameStatus;
  winner: Player | null;            // statusが "win" の時のみ値がある
  winning_pattern: number[] | null; // 勝利した組み合わせ，例 [0, 1, 2]
};