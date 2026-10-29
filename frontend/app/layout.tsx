// frontend/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

// ページのタイトル（元の index.html の <title> と同じ）
export const metadata: Metadata = {
  title: "TIC TAC TOE",
};

// 全ページ共通のレイアウト。必ず default export の React コンポーネントにする
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}