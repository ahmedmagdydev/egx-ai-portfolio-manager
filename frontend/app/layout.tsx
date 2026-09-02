import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EGX AI Portfolio Manager",
  description: "Phase 00 local bootstrap",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" dir="ltr">
      <body>{children}</body>
    </html>
  );
}
