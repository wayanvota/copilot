import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";

const port = Number(process.env.PORT || 4193);
const root = path.resolve("out");
const types = { ".css": "text/css", ".html": "text/html", ".js": "text/javascript", ".svg": "image/svg+xml", ".txt": "text/plain", ".xml": "application/xml" };

createServer((req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
  let relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
  if (relative === "copilot" || relative.startsWith("copilot/")) {
    relative = relative.slice("copilot".length).replace(/^\/+/, "");
  }
  if (!relative || relative.endsWith("/")) relative += "index.html";
  const target = path.resolve(root, relative);
  if (!target.startsWith(`${root}${path.sep}`)) {
    res.writeHead(404, { "X-Content-Type-Options": "nosniff" });
    return res.end("Not found");
  }
  try {
    if (!statSync(target).isFile()) throw new Error("not a file");
    res.writeHead(200, { "Content-Type": types[path.extname(target)] || "application/octet-stream", "X-Content-Type-Options": "nosniff" });
    createReadStream(target).pipe(res);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain", "X-Content-Type-Options": "nosniff" });
    res.end("Not found");
  }
}).listen(port, "127.0.0.1", () => console.log(`Copilot static fixture listening on ${port}`));
