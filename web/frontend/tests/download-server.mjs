// Serve actual bytes through Vite's proxy so browser tests verify download
// completion/content, rather than only a mocked Content-Disposition event.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";

const bytes = readFileSync(new URL("./fixtures/result.json", import.meta.url));
const id = JSON.parse(bytes).job_id;
createServer((request, response) => {
  if (request.url === "/health") {
    response.end("ok");
    return;
  }
  if (request.url === `/api/v1/design-jobs/${id}/artifacts/result-json`) {
    response.writeHead(200, {
      "Content-Type": "application/json",
      "Content-Length": bytes.length,
      "Content-Disposition": 'attachment; filename="result.json"',
    });
    response.end(bytes);
    return;
  }
  response.writeHead(404);
  response.end("Test fixture route not found");
}).listen(18081, "127.0.0.1");
