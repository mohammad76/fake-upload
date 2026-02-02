#!/usr/bin/env python3
"""
High-Performance Server for Receiving Fake Uploads
This server receives data but doesn't store it - optimized for parallel connections
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import argparse
import time
from datetime import datetime
import threading

class UploadHandler(BaseHTTPRequestHandler):
    total_received = 0
    request_count = 0
    start_time = time.time()
    stats_lock = threading.Lock()
    
    def do_POST(self):
        """Receive POST request and count data"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read all data at once if not too large, otherwise chunk it
            if content_length < 50 * 1024 * 1024:  # Less than 50MB
                data = self.rfile.read(content_length)
                bytes_read = len(data)
            else:
                # Read in chunks for large uploads
                bytes_read = 0
                chunk_size = 8192
                while bytes_read < content_length:
                    remaining = content_length - bytes_read
                    to_read = min(chunk_size, remaining)
                    chunk = self.rfile.read(to_read)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
            
            # Update statistics (thread-safe)
            with UploadHandler.stats_lock:
                UploadHandler.total_received += bytes_read
                UploadHandler.request_count += 1
            
            # Send success response
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', '2')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                self.wfile.write(b'OK')
            except (BrokenPipeError, ConnectionResetError, OSError):
                # Client closed connection, that's fine
                pass
            
        except Exception as e:
            # Silently ignore errors
            pass
    
    def do_GET(self):
        """Display stats on GET request"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            with UploadHandler.stats_lock:
                total = UploadHandler.total_received
                count = UploadHandler.request_count
            
            elapsed = time.time() - UploadHandler.start_time
            speed = total / elapsed if elapsed > 0 else 0
            
            html = f"""
            <html>
            <head>
                <title>Fake Upload Server Stats</title>
                <meta charset="utf-8">
                <meta http-equiv="refresh" content="1">
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        min-height: 100vh;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                    }}
                    .stats {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 15px; 
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        margin-bottom: 20px;
                    }}
                    h1 {{ 
                        color: #333; 
                        margin: 0 0 30px 0;
                        font-size: 28px;
                        text-align: center;
                    }}
                    .metrics {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                    }}
                    .metric {{ 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 10px;
                        color: white;
                        text-align: center;
                    }}
                    .metric-label {{
                        font-size: 14px;
                        opacity: 0.9;
                        margin-bottom: 10px;
                    }}
                    .value {{ 
                        font-size: 32px; 
                        font-weight: bold;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }}
                    .footer {{
                        text-align: center;
                        color: white;
                        font-size: 14px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="stats">
                        <h1>📊 Fake Upload Server Statistics</h1>
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-label">Total Received</div>
                                <div class="value">{self.format_bytes(total)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Upload Speed</div>
                                <div class="value">{self.format_bytes(speed)}/s</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Requests</div>
                                <div class="value">{count:,}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Uptime</div>
                                <div class="value">{self.format_time(elapsed)}</div>
                            </div>
                        </div>
                    </div>
                    <div class="footer">
                        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        except:
            pass
    
    def format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def format_time(self, seconds):
        """Format seconds to human readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"
    
    def log_message(self, format, *args):
        """Disable default logs"""
        pass
    
    def handle(self):
        """Handle request with error suppression"""
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Client closed connection early, ignore
            pass


class StatsDisplay:
    """Display live statistics in console"""
    def __init__(self):
        self.running = True
        self.last_bytes = 0
        self.last_time = time.time()
    
    def run(self):
        """Update console stats periodically"""
        while self.running:
            time.sleep(1)
            
            current_time = time.time()
            with UploadHandler.stats_lock:
                current_bytes = UploadHandler.total_received
                total_requests = UploadHandler.request_count
            
            elapsed = current_time - UploadHandler.start_time
            
            # Calculate instantaneous speed
            time_delta = current_time - self.last_time
            bytes_delta = current_bytes - self.last_bytes
            instant_speed = bytes_delta / time_delta if time_delta > 0 else 0
            
            # Calculate average speed
            avg_speed = current_bytes / elapsed if elapsed > 0 else 0
            
            self.last_bytes = current_bytes
            self.last_time = current_time
            
            # Format output
            total_str = self.format_bytes(current_bytes)
            instant_str = self.format_bytes(instant_speed)
            avg_str = self.format_bytes(avg_speed)
            
            stats = (f"\r📥 Received: {total_str} | "
                    f"Speed: {instant_str}/s (avg: {avg_str}/s) | "
                    f"Requests: {total_requests:,} | "
                    f"Time: {int(elapsed)}s")
            
            print(stats, end='', flush=True)
    
    def format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}PB"
    
    def stop(self):
        """Stop the stats display"""
        self.running = False


def main():
    parser = argparse.ArgumentParser(
        description='High-performance server for receiving fake uploads',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help='Server port (default: 8080)')
    
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                        help='Listen address (default: 0.0.0.0 - all interfaces)')
    
    args = parser.parse_args()
    
    # Use ThreadingHTTPServer for better parallel connection handling
    server_address = (args.host, args.port)
    httpd = ThreadingHTTPServer(server_address, UploadHandler)
    httpd.daemon_threads = True  # Don't wait for threads on shutdown
    
    print(f"\n{'='*70}")
    print(f"🚀 High-Performance Fake Upload Server Started")
    print(f"{'='*70}")
    print(f"Listening on: {args.host}:{args.port}")
    print(f"Web interface: http://localhost:{args.port}")
    print(f"Server supports parallel connections (multi-threaded)")
    print(f"Press Ctrl+C to stop")
    print(f"{'='*70}\n")
    
    # Start stats display in background
    stats_display = StatsDisplay()
    stats_thread = threading.Thread(target=stats_display.run, daemon=True)
    stats_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped")
        stats_display.stop()
        
        elapsed = time.time() - UploadHandler.start_time
        with UploadHandler.stats_lock:
            total = UploadHandler.total_received
            count = UploadHandler.request_count
        
        print(f"\n{'='*70}")
        print(f"Final Statistics:")
        print(f"{'='*70}")
        
        handler = UploadHandler(None, None, None)
        print(f"Total Received: {handler.format_bytes(total)}")
        print(f"Total Requests: {count:,}")
        print(f"Total Time: {int(elapsed)} seconds ({elapsed/3600:.2f} hours)")
        
        if elapsed > 0:
            speed = total / elapsed
            print(f"Average Speed: {handler.format_bytes(speed)}/s")
        
        if count > 0:
            avg_per_request = total / count
            print(f"Average per Request: {handler.format_bytes(avg_per_request)}")
        
        print(f"{'='*70}\n")
    
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
