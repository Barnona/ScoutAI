import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL
  ? new URL(process.env.NEXT_PUBLIC_SITE_URL)
  : undefined;

export const metadata = {
  ...(siteUrl ? { metadataBase: siteUrl } : {}),
  title: {
    default: "ScoutAI // Research Command",
    template: "%s // ScoutAI",
  },
  description:
    "ScoutAI is an autonomous research agent that plans, searches, verifies, challenges conflicting evidence, and synthesizes cited intelligence briefs.",
  applicationName: "ScoutAI",
  keywords: [
    "ScoutAI",
    "AI research agent",
    "autonomous research",
    "evidence-based research",
    "AI research",
    "research assistant",
  ],
  authors: [{ name: "ScoutAI" }],
  creator: "ScoutAI",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  openGraph: {
    title: "ScoutAI // Research Command",
    description:
      "Autonomous research that plans, searches, verifies, challenges, and synthesizes evidence.",
    type: "website",
    siteName: "ScoutAI",
  },
  twitter: {
    card: "summary",
    title: "ScoutAI // Research Command",
    description:
      "Autonomous research that plans, searches, verifies, challenges, and synthesizes evidence.",
  },
  robots: {
    index: true,
    follow: true,
    "max-image-preview": "large",
    "max-snippet": -1,
    "max-video-preview": -1,
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
