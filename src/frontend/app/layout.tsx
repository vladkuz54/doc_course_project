import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  weight: ["400", "600"],
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "Автопарк",
  description: "Керування автопарком",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="uk" className={plexSans.className}>
      <body>{children}</body>
    </html>
  );
}
