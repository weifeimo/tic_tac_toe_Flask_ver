// frontend/components/Cell.tsx
import type { Cell as CellValue } from "@/types/game";
import styles from "./game.module.css";

type Props = {
  value: CellValue;       // null = 未配置, 0 = X, 1 = O
  isWinning: boolean;     // 勝利ラインに含まれるマスか
  disabled: boolean;      // クリック不可にするか
  onClick: () => void;
};

/** 盤面の1マス */
export default function Cell({ value, isWinning, disabled, onClick }: Props) {
  const mark = value === 0 ? "X" : value === 1 ? "O" : "";

  return (
    <button
      type="button"
      className={`${styles.cell} ${isWinning ? styles.winner : ""}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={mark ? `マス ${mark}` : "空きマス"}
    >
      {mark}
    </button>
  );
}