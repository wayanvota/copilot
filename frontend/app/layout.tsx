import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://wayan.com"),
  title: "Nebraska Pork Compliance Copilot",
  description: "Evidence-backed compliance answers for Nebraska pork producers.",
  alternates: { canonical: "/copilot/" },
  icons: {
    icon: [{ url: "/tool-assets/wayan-favicon.ico", sizes: "32x32", type: "image/x-icon" }],
    shortcut: "/tool-assets/wayan-favicon.ico",
  },
  openGraph: {
    type: "website",
    url: "/copilot/",
    title: "Nebraska Pork Compliance Copilot",
    description: "Evidence-backed compliance answers for Nebraska pork producers.",
    siteName: "Wayan Vota AI Tools",
    images: [
      {
        url: "/tool-assets/wayan-ai-tools-share.jpg",
        width: 1200,
        height: 627,
        alt: "AI tools built by Wayan. Practical prototypes with visible evidence and human judgment.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@wayan_vota",
    title: "Nebraska Pork Compliance Copilot",
    description: "Evidence-backed compliance answers for Nebraska pork producers.",
    images: ["/tool-assets/wayan-ai-tools-share.jpg"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
