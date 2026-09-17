import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Verify email",
  robots: { index: false, follow: false },
  alternates: { canonical: "/verify-email" },
};

export default function VerifyEmailLayout({ children }: { children: React.ReactNode }) {
  return children;
}
