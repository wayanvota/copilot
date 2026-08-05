import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Iowa Pork Compliance Copilot",
  description: "Evidence-backed compliance answers for Iowa pork producers.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
