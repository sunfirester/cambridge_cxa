import http.server
import socketserver
import subprocess
import logging

PORT = 5001

logging.basicConfig(level=logging.INFO)

class CXA_IR_Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/vol/up":
            logging.info("Volume UP requested")
            subprocess.run(["ir-ctl", "-d", "/dev/lirc0", "-S", "rc5:0x1010"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/vol/down":
            logging.info("Volume DOWN requested")
            subprocess.run(["ir-ctl", "-d", "/dev/lirc0", "-S", "rc5:0x1011"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

with socketserver.TCPServer(("", PORT), CXA_IR_Handler) as httpd:
    logging.info(f"Serving CXA IR Bridge on port {PORT}")
    httpd.serve_forever()
