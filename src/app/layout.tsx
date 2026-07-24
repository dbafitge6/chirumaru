import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ちるまる | 新潟のカフェ・パン屋・スイーツ探し",
  description:
    "新潟県内のカフェ・パン屋・スイーツ店・喫茶店をエリアやタグでゆるっと探せるお店探しサイト、ちるまる。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-cream text-umber">
        {children}
      </body>
    </html>
  );
}
