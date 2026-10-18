// The maintained merged app serves public pages and /admin from one server.
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const index = args.findIndex((arg) => arg === '-p' || arg === '--port');
const port = index >= 0 ? args[index + 1] : process.env.PORT || '3000';
const child = spawn(process.execPath, [path.join(root, 'node_modules/next/dist/bin/next'), 'dev', '--webpack', '--port', port], {
  cwd: path.join(root, 'landing'), env: process.env, stdio: 'inherit',
});
child.on('exit', (code) => process.exit(code ?? 0));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
