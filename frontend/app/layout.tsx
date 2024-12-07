import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
// import '@fortawesome/fontawesome-svg-core/styles.css'; // Import Font Awesome styles
// import { config } from '@fortawesome/fontawesome-svg-core';

// config.autoAddCss = false;
const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Calorie and Diet Plan Assistant",
  description:
    "Website powered by AI agent that can help you in making your personalized diet and calorie plan.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
