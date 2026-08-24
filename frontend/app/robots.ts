import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/copilot/", disallow: "/copilot/admin/" }],
    sitemap: "https://wayan.com/copilot/sitemap.xml",
  };
}
