import http.server
import socketserver
import os

PORT = 8765
DIRECTORY = r"D:\FieldVision AI\.superpowers\brainstorm\session\content"

os.chdir(DIRECTORY)

handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()
