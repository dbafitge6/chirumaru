import type { Metadata } from "next";
import Script from "next/script";
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
      <head>
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-TV092FWCKR"
          strategy="afterInteractive"
        />
        <Script id="ga4-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-TV092FWCKR');
          `}
        </Script>
      </head>
      <body className="min-h-full flex flex-col bg-cream text-umber">
        {children}
      </body>
    </html>
  );
}
