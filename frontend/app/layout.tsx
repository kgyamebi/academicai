import type { Metadata } from "next";
import { Newsreader, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { messages } from "@/lib/i18n";
import { siteUrl } from "@/lib/utils";
import { SentryInit } from "@/components/SentryInit";
import { GoogleAdsInit } from "@/components/GoogleAdsInit";

const sans = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-sans" });
const serif = Newsreader({ subsets: ["latin"], variable: "--font-serif" });

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: {
    default: "Free Assignment, Thesis & Citation Checker | AcademicCheck AI",
    template: `%s | ${messages.product}`,
  },
  description:
    "Get actionable feedback on your assignment’s thesis, argument, evidence, structure and citations before submission. Free first check.",
  applicationName: messages.product,
  icons: {
    icon: [{ url: "/brand/mark.png", type: "image/png", sizes: "512x512" }],
    apple: [{ url: "/brand/mark.png", type: "image/png", sizes: "180x180" }],
  },
  openGraph: {
    title: "Free Assignment, Thesis & Citation Checker | AcademicCheck AI",
    description:
      "Get actionable feedback on your assignment’s thesis, argument, evidence, structure and citations before submission. Free first check.",
    type: "website",
    url: "/",
    siteName: messages.product,
    images: [
      {
        url: "/brand/og.png",
        width: 1200,
        height: 630,
        alt: "AcademicCheck AI — assignment, thesis and citation diagnostics before you submit.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Free Assignment, Thesis & Citation Checker | AcademicCheck AI",
    description:
      "Get actionable feedback on your assignment’s thesis, argument, evidence, structure and citations before submission. Free first check.",
    images: ["/brand/og.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable}`}>
      <body className="min-h-screen antialiased">
        <SentryInit />
        <GoogleAdsInit />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-[var(--paper-2)] focus:px-3 focus:py-2"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
