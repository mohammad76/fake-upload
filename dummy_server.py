#!/usr/bin/env python3
"""
Simple server for receiving fake uploads
This server receives data but doesn't store it
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import time
from datetime import datetime

class UploadHandler(BaseHTTPRequestHandler):
    total_received = 0
    start_time = time.time()
    
    def do_POST(self):
        """Receive POST request and count data"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Read data in small chunks
        bytes_read = 0
        chunk_size = 8192
        
        while bytes_read < content_length:
            remaining = content_length - bytes_read
            to_read = min(chunk_size, remaining)
            chunk = self.rfile.read(to_read)
            bytes_read += len(chunk)
            UploadHandler.total_received += len(chunk)
        
        # Send success response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
        
        # Display stats
        self.print_stats()
    
    def do_GET(self):
        """Display stats on GET request"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        elapsed = time.time() - UploadHandler.start_time
        speed = UploadHandler.total_received / elapsed if elapsed > 0 else 0
        
        html = f"""
        <html>
        <head>
            <title>Fake Upload Server Stats</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="2">
            <style>
                body {{ font-family: Arial; padding: 20px; background: #f0f0f0; }}
                .stats {{ background: white; padding: 20px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .metric {{ margin: 15px 0; padding: 10px; background: #f9f9f9; border-left: 4px solid #4CAF50; }}
                .value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="stats">
                <h1>📊 Fake Upload Server Stats</h1>
                <div class="metric">
                    <div>Total Received:</div>
                    <div class="value">{self.format_bytes(UploadHandler.total_received)}</div>
                </div>
                <div class="metric">
                    <div>Uptime:</div>
                    <div class="value">{int(elapsed)} seconds</div>
                </div>
                <div class="metric">
                    <div>Average Speed:</div>
                    <div class="value">{self.format_bytes(speed)}/s</div>
                </div>
                <div class="metric">
                    <div>Last Updated:</div>
                    <div>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def print_stats(self):
        """Print stats to console"""
        elapsed = time.time() - UploadHandler.start_time
        speed = UploadHandler.total_received / elapsed if elapsed > 0 else 0
        
        stats = (f"\r📥 Received: {self.format_bytes(UploadHandler.total_received)} | "
                f"Speed: {self.format_bytes(speed)}/s | "
                f"Time: {int(elapsed)}s")
        print(stats, end='', flush=True)
    
    def log_message(self, format, *args):
        """Disable default logs"""
        pass


def main():
    parser = argparse.ArgumentParser(
        description='Simple server for receiving fake uploads',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help='Server port (default: 8080)')
    
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                        help='Listen address (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, UploadHandler)
    
    print(f"\n{'='*60}")
    print(f"🚀 Fake Upload Server Started")
    print(f"{'='*60}")
    print(f"Address: http://{args.host}:{args.port}")
    print(f"View stats at: http://localhost:{args.port}")
    print(f"Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped")
        elapsed = time.time() - UploadHandler.start_time
        print(f"\n{'='*60}")
        print(f"Final Stats:")
        print(f"Total Received: {UploadHandler(None, None, None).format_bytes(UploadHandler.total_received)}")
        print(f"Total Time: {int(elapsed)} seconds")
        if elapsed > 0:
            speed = UploadHandler.total_received / elapsed
            print(f"Average Speed: {UploadHandler(None, None, None).format_bytes(speed)}/s")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
