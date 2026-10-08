const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '../build/web');
const port = Number(process.argv[2] || 4177);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.mjs': 'application/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2' };

// Flutter's development server and the Firebase Hosting emulator don't provide
// media byte ranges. Use this local server to exercise the same seek behavior
// as deployed Firebase Hosting, including cold and cached video requests.
const server = http.createServer((request, response) => {
  let file;
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    file = path.resolve(root, `.${pathname}`);
    if (file !== root && !file.startsWith(`${root}${path.sep}`)) {
      response.writeHead(403).end();
      return;
    }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) file = path.join(root, 'index.html');
    const stat = fs.statSync(file);
    const extension = path.extname(file);
    const relative = path.relative(root, file).split(path.sep).join('/');
    const cache = /^canvaskit\/[a-f0-9]+\//.test(relative)
      ? 'public, max-age=31536000, immutable'
      : /\.(woff2|ttf|otf|png|jpg|jpeg|svg|mp4|bin)$/.test(file)
        ? 'public, max-age=3600'
        : 'no-cache';
    response.setHeader('Content-Type', types[extension] || 'application/octet-stream');
    response.setHeader('Cache-Control', cache);
    response.setHeader('Accept-Ranges', 'bytes');
    let start = 0;
    let end = stat.size - 1;
    const range = request.headers.range;
    if (range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(range);
      if (match && (match[1] || match[2])) {
        start = match[1] ? Number(match[1]) : Math.max(0, stat.size - Number(match[2]));
        end = match[1] && match[2] ? Math.min(Number(match[2]), end) : end;
      } else start = stat.size;
      if (start > end || start >= stat.size) {
        response.writeHead(416, { 'Content-Range': `bytes */${stat.size}` }).end();
        return;
      }
      response.statusCode = 206;
      response.setHeader('Content-Range', `bytes ${start}-${end}/${stat.size}`);
    }
    const gzip = !range && /\.(html|js|mjs|wasm|json|svg)$/.test(file) && /\bgzip\b/.test(request.headers['accept-encoding'] || '');
    if (gzip) {
      response.setHeader('Content-Encoding', 'gzip');
      response.setHeader('Vary', 'Accept-Encoding');
    } else response.setHeader('Content-Length', end - start + 1);
    if (request.method === 'HEAD') { response.end(); return; }
    const stream = fs.createReadStream(file, { start, end });
    stream.on('error', () => response.destroy());
    response.on('close', () => stream.destroy());
    if (gzip) stream.pipe(zlib.createGzip()).pipe(response);
    else stream.pipe(response);
  } catch (error) {
    response.writeHead(500).end(error.message);
  }
});
server.listen(port, '127.0.0.1', () => console.log(`Release preview: http://127.0.0.1:${port}`));
