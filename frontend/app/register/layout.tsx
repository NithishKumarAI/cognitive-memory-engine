import type { Metadata } from "next";
import { branding } from "@/lib/branding";

export const metadata: Metadata = { title: `Create account | ${branding.name}`, description: branding.description };

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return children;
}
