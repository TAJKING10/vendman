/* Local dev server with the same clean-URL behaviour as production.
   Run: node serve.js   ->   http://127.0.0.1:8000
   Static files are served as-is; the slugs below fall back to index.html. */
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const PORT = process.env.PORT || 8000;
const SLUGS = ['machines', 'solutions', 'services', 'about', 'contact', 'privacy-policy', 'terms'];
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.mp4': 'video/mp4', '.webm': 'video/webm', '.pdf': 'application/pdf'
};

http.createServer((req, res) => {
  let pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const slug = pathname.replace(/^\/+|\/+$/g, '');

  if (pathname === '/' || SLUGS.includes(slug)) pathname = '/index.html';

  const file = path.join(ROOT, pathname);
  if (!file.startsWith(ROOT)) { res.writeHead(403).end('Forbidden'); return; }

  const type = TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream';

  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) { res.writeHead(404, { 'Content-Type': 'text/plain' }).end('404 Not Found'); return; }

    /* Range support. Without it a browser cannot seek a <video> at all, so the
       loops here could only ever be played from the start locally — production
       serves ranges, so this keeps dev honest. */
    const range = req.headers.range;
    if (range) {
      const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
      if (m) {
        let start = m[1] === '' ? stat.size - Number(m[2]) : Number(m[1]);
        let end = m[1] === '' || m[2] === '' ? stat.size - 1 : Number(m[2]);
        if (Number.isNaN(start) || Number.isNaN(end) || start > end || start < 0 || end >= stat.size) {
          res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` }).end();
          return;
        }
        res.writeHead(206, {
          'Content-Type': type,
          'Content-Length': end - start + 1,
          'Content-Range': `bytes ${start}-${end}/${stat.size}`,
          'Accept-Ranges': 'bytes',
          'Cache-Control': 'no-cache'
        });
        fs.createReadStream(file, { start, end }).pipe(res);
        return;
      }
    }

    res.writeHead(200, {
      'Content-Type': type,
      'Content-Length': stat.size,
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'no-cache'
    });
    fs.createReadStream(file).pipe(res);
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log(`Vendman dev server: http://127.0.0.1:${PORT}`);
});
