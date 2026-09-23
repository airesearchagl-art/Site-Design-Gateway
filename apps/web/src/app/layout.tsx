import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Site Design Gateway",
  description: "敷地・計画条件を整理し、計算済みの初期ボリューム案を建築面積・延床面積・階数・高さで比較します。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ja"><body>{children}</body></html>;
}
