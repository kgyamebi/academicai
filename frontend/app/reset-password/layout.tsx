import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Set new password",
  robots: { index: false, follow: false },
  alternates: { canonical: "/reset-password" },
};

export default function ResetPasswordLayout({ children }: { children: React.ReactNode }) {
  return children;
}
