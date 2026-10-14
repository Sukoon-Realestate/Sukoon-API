// Runs both frontend zones for local dev:
//   landing  → http://localhost:<port>        (default 3000, public entry point)
//   admin    → http://localhost:<port>/admin  (proxied to the admin server on ADMIN_PORT)
// Usage: node scripts/dev.mjs [-p 3000]   (the port flag matches `next dev -p`)
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const flag = args.findIndex((a) => a === "-p" || a === "--port");
const landingPort = flag >= 0 ? args[flag + 1] : process.env.PORT || "3000";
const adminPort = process.env.ADMIN_PORT || "3001";

const zones = [
  { name: "admin  ", color: 36, cwd: root, port: adminPort, env: {} },
  {
    name: "landing",
    color: 32,
    cwd: path.join(root, "landing"),
    port: landingPort,
    env: { ADMIN_URL: `http://localhost:${adminPort}` },
  },
];

const children = zones.map((zone) => {
  // Drop PORT (set by backend/scripts/dev.py) so each zone uses its own --port.
  const env = { ...process.env, ...zone.env };
  delete env.PORT;
  const child = spawn("npx", ["next", "dev", "--port", zone.port], {
    cwd: zone.cwd,
    env,
    shell: true,
  });
  const prefix = `\x1b[${zone.color}m[${zone.name}]\x1b[0m `;
  for (const stream of [child.stdout, child.stderr]) {
    stream.on("data", (chunk) => {
      for (const line of chunk.toString().split(/\r?\n/)) if (line) console.log(prefix + line);
    });
  }
  child.on("exit", (code) => {
    console.log(`${prefix}exited with code ${code}`);
    shutdown(code ?? 0);
  });
  return child;
});

console.log(`\nSukoon frontend → http://localhost:${landingPort}  (admin: http://localhost:${landingPort}/admin)\n`);

let stopping = false;
function shutdown(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode !== null) continue;
    // With shell: true, kill() only stops the shell on Windows; take down the whole tree.
    if (process.platform === "win32") spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"]);
    else child.kill();
  }
  setTimeout(() => process.exit(code), 500);
}
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
