import type { Metadata } from "next";
import "./globals.css";
import { branding } from "@/lib/branding";
import { themeBootstrap } from "@/lib/theme";

export const metadata: Metadata = {
  title: branding.name,
  description: branding.description,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeBootstrap }} /></head>
      <body className="min-h-full bg-background text-foreground">{children}</body>
    </html>
  );
}
