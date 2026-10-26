// frontend/components/Board.tsx
import type { Cell as CellValue } from "@/types/game";
import Cell from "./Cell";
import styles from "./game.module.css";

type Props = {
  cells: CellValue[];                 // 長さ 9 の盤面
  winningPattern: number[] | null;    // 勝利ライン（例: [0, 1, 2]）
  disabled: boolean;                  // 通信中・ゲーム終了時は true
  onCellClick: (index: number) => void;
};

/** 3x3 の盤面。各マスの表示と操作可否を決めて Cell に渡す */
export default function Board({ cells, winningPattern, disabled, onCellClick }: Props) {
  return (
    <div className={styles.board}>
      {cells.map((value, index) => (
        <Cell
          key={index}
          value={value}
          isWinning={winningPattern?.includes(index) ?? false}
          // すでに埋まっているマスは押せないようにする
          disabled={disabled || value !== null}
          onClick={() => onCellClick(index)}
        />
      ))}
    </div>
  );
}