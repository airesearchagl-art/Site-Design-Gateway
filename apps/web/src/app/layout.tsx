import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Site Design Gateway",
  description: "建築初期検討のProject JSONと出典状態を確認するGateway。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ja"><body>{children}</body></html>;
}
