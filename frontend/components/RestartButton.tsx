// frontend/components/RestartButton.tsx
import styles from "./game.module.css";

type Props = {
  disabled: boolean;
  onClick: () => void;
};

/** 新しいゲームを開始するボタン（元の #restart に相当） */
export default function RestartButton({ disabled, onClick }: Props) {
  return (
    <button
      type="button"
      className={styles.restart}
      onClick={onClick}
      disabled={disabled}
    >
      RESTART
    </button>
  );
}