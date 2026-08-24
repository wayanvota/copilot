import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://wayan.com"),
  title: "Nebraska Pork Compliance Copilot",
  description: "Evidence-backed compliance answers for Nebraska pork producers.",
  alternates: { canonical: "/copilot/" },
  openGraph: {
    type: "website",
    url: "/copilot/",
    title: "Nebraska Pork Compliance Copilot",
    description: "Evidence-backed compliance answers for Nebraska pork producers.",
    siteName: "Nebraska Pork Compliance Copilot",
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
