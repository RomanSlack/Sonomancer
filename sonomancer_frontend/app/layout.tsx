import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sonomancer - Ambient E-Reader",
  description: "An immersive e-reading experience with AI-generated ambient soundscapes",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-gray-900 text-gray-100`}>
        {children}
      </body>
    </html>
  );
}