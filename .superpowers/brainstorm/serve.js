const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8765;
const DIR = 'D:\\FieldVision AI\\.superpowers\\brainstorm\\session\\content';

const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript' };

const server = http.createServer((req, res) => {
  const file = path.join(DIR, req.url === '/' ? 'system-architecture.html' : req.url);
  if (!fs.existsSync(file)) { res.writeHead(404); res.end('Not found'); return; }
  const ext = path.extname(file);
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/html' });
  res.end(fs.readFileSync(file));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
