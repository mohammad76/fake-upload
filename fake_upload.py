#!/usr/bin/env python3
"""
Fake Upload Generator
This script simulates upload traffic to increase server upload statistics
"""

import argparse
import time
import random
import socket
import sys
from datetime import datetime, timedelta
from threading import Thread, Event
import signal

class FakeUploader:
    def __init__(self, target_host, target_port, daily_gb, chunk_size_mb=10, 
                 continuous=False, duration_hours=24):
        """
        Initialize the fake uploader
        
        Args:
            target_host: Target server address
            target_port: Server port
            daily_gb: Gigabytes to upload per day
            chunk_size_mb: Size of each data chunk in megabytes
            continuous: Continuous upload or stop after reaching target
            duration_hours: Duration in hours
        """
        self.target_host = target_host
        self.target_port = target_port
        self.daily_gb = daily_gb
        self.chunk_size_mb = chunk_size_mb
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.continuous = continuous
        self.duration_hours = duration_hours
        
        # Calculate values
        self.total_bytes = daily_gb * 1024 * 1024 * 1024
        self.bytes_per_second = self.total_bytes / (duration_hours * 3600)
        
        # Statistics
        self.uploaded_bytes = 0
        self.start_time = None
        self.stop_event = Event()
        
    def generate_random_data(self, size):
        """Generate random data for upload"""
        # Use random data for more realistic simulation
        return bytes(random.getrandbits(8) for _ in range(size))
    
    def format_bytes(self, bytes_val):
        """Format bytes to human readable unit"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def calculate_speed(self, bytes_uploaded, elapsed_seconds):
        """Calculate upload speed"""
        if elapsed_seconds == 0:
            return "0 B/s"
        speed = bytes_uploaded / elapsed_seconds
        return f"{self.format_bytes(speed)}/s"
    
    def print_progress(self):
        """Display upload progress"""
        if self.start_time is None:
            return
            
        elapsed = time.time() - self.start_time
        progress = (self.uploaded_bytes / self.total_bytes) * 100 if not self.continuous else 0
        speed = self.calculate_speed(self.uploaded_bytes, elapsed)
        
        if self.continuous:
            status = f"Uploaded: {self.format_bytes(self.uploaded_bytes)} | Speed: {speed} | Time: {int(elapsed)}s"
        else:
            status = f"Progress: {progress:.1f}% | Uploaded: {self.format_bytes(self.uploaded_bytes)} / {self.format_bytes(self.total_bytes)} | Speed: {speed}"
        
        print(f"\r{status}", end='', flush=True)
    
    def send_to_discard_server(self, data):
        """
        Send data to discard server
        Discard server (port 9) receives data but doesn't respond
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.target_host, self.target_port))
            sock.sendall(data)
            sock.close()
            return True
        except Exception as e:
            return False
    
    def send_to_http_server(self, data):
        """Send data to HTTP server using POST method"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.target_host, self.target_port))
            
            # Build HTTP POST request
            content_length = len(data)
            request = (
                f"POST /upload HTTP/1.1\r\n"
                f"Host: {self.target_host}\r\n"
                f"Content-Length: {content_length}\r\n"
                f"Content-Type: application/octet-stream\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode() + data
            
            sock.sendall(request)
            sock.close()
            return True
        except Exception as e:
            return False
    
    def upload_chunk(self):
        """Upload a data chunk"""
        data = self.generate_random_data(self.chunk_size_bytes)
        
        # Try to send to server
        success = False
        if self.target_port == 9:
            success = self.send_to_discard_server(data)
        else:
            success = self.send_to_http_server(data)
        
        if success:
            self.uploaded_bytes += len(data)
            return True
        return False
    
    def run(self):
        """Run fake upload"""
        print(f"\n{'='*60}")
        print(f"Starting Fake Upload")
        print(f"{'='*60}")
        print(f"Target: {self.target_host}:{self.target_port}")
        print(f"Goal: {self.daily_gb} GB in {self.duration_hours} hours")
        print(f"Target Speed: {self.format_bytes(self.bytes_per_second)}/s")
        print(f"Chunk Size: {self.chunk_size_mb} MB")
        print(f"Mode: {'Continuous' if self.continuous else 'Limited'}")
        print(f"{'='*60}\n")
        print("Press Ctrl+C to stop\n")
        
        self.start_time = time.time()
        end_time = self.start_time + (self.duration_hours * 3600)
        
        try:
            while not self.stop_event.is_set():
                # Check end time
                current_time = time.time()
                if not self.continuous and current_time >= end_time:
                    break
                
                # Check if target reached
                if not self.continuous and self.uploaded_bytes >= self.total_bytes:
                    break
                
                # Calculate delay for speed control
                elapsed = current_time - self.start_time
                expected_bytes = self.bytes_per_second * elapsed
                
                if self.uploaded_bytes < expected_bytes:
                    # Upload a chunk
                    if self.upload_chunk():
                        self.print_progress()
                    else:
                        # If upload failed, wait a bit
                        time.sleep(1)
                else:
                    # Control speed
                    time.sleep(0.1)
                    self.print_progress()
            
            # Display final result
            print("\n")
            print(f"\n{'='*60}")
            print("Upload Completed!")
            print(f"{'='*60}")
            total_time = time.time() - self.start_time
            avg_speed = self.calculate_speed(self.uploaded_bytes, total_time)
            print(f"Total Uploaded: {self.format_bytes(self.uploaded_bytes)}")
            print(f"Total Time: {int(total_time)} seconds ({total_time/3600:.2f} hours)")
            print(f"Average Speed: {avg_speed}")
            print(f"{'='*60}\n")
            
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            self.stop_event.set()
    
    def stop(self):
        """Stop upload"""
        self.stop_event.set()


def signal_handler(sig, frame):
    """Handle Ctrl+C signal"""
    print("\n\nReceived stop signal...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Fake Upload Generator - Network Traffic Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  
  # Upload 400GB in 24 hours to local server:
  python fake_upload.py -g 400
  
  # Upload 100GB in 12 hours:
  python fake_upload.py -g 100 -d 12
  
  # Continuous upload at 50GB per day rate:
  python fake_upload.py -g 50 -c
  
  # Upload to specific server:
  python fake_upload.py -g 200 -H example.com -p 80
  
  # Set custom chunk size:
  python fake_upload.py -g 100 -s 5
        """
    )
    
    parser.add_argument('-g', '--gigabytes', type=float, required=True,
                        help='Gigabytes to upload (example: 400)')
    
    parser.add_argument('-H', '--host', type=str, default='localhost',
                        help='Target server address (default: localhost)')
    
    parser.add_argument('-p', '--port', type=int, default=9,
                        help='Server port (default: 9 - discard service)')
    
    parser.add_argument('-s', '--chunk-size', type=int, default=10,
                        help='Chunk size in megabytes (default: 10)')
    
    parser.add_argument('-d', '--duration', type=float, default=24,
                        help='Upload duration in hours (default: 24)')
    
    parser.add_argument('-c', '--continuous', action='store_true',
                        help='Continuous upload without limit')
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and run uploader
    uploader = FakeUploader(
        target_host=args.host,
        target_port=args.port,
        daily_gb=args.gigabytes,
        chunk_size_mb=args.chunk_size,
        continuous=args.continuous,
        duration_hours=args.duration
    )
    
    try:
        uploader.run()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
