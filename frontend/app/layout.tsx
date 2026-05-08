import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Caprae AI-Readiness Scorer",
  description:
    "Surface the lower-middle-market B2B SaaS companies most ready for post-acquisition AI value creation.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
