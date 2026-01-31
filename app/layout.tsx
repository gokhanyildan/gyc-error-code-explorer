import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Error Code Explorer | Gökhan Yıldan",
  description:
    "Search and filter Windows, Linux, Web/HTTP, Network, Database, Container, and SMTP error codes with runbooks.",
  authors: [{ name: "Gökhan Yıldan", url: "https://gokhanyildan.com" }],
  openGraph: {
    title: "Error Code Explorer | Gökhan Yıldan",
    description:
      "Professional error code explorer with filtering, context tags, and runbooks.",
    siteName: "Error Code Explorer",
    type: "website",
  },
  icons: {
    icon: "/icon.svg",
  },
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
