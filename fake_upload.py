#!/usr/bin/env python3
"""
Fake Upload Generator with Parallel Upload Support
This script simulates upload traffic to increase server upload statistics
"""

import argparse
import time
import random
import socket
import sys
from datetime import datetime
from threading import Thread, Event, Lock
import signal

class ParallelUploader:
    def __init__(self, target_host, target_port, daily_gb, chunk_size_mb=10, 
                 continuous=False, duration_hours=24, threads=4):
        """
        Initialize the parallel fake uploader
        
        Args:
            target_host: Target server address
            target_port: Server port
            daily_gb: Gigabytes to upload per day
            chunk_size_mb: Size of each data chunk in megabytes
            continuous: Continuous upload or stop after reaching target
            duration_hours: Duration in hours
            threads: Number of parallel upload threads
        """
        self.target_host = target_host
        self.target_port = target_port
        self.daily_gb = daily_gb
        self.chunk_size_mb = chunk_size_mb
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.continuous = continuous
        self.duration_hours = duration_hours
        self.num_threads = threads
        
        # Calculate values
        self.total_bytes = daily_gb * 1024 * 1024 * 1024
        self.bytes_per_second = self.total_bytes / (duration_hours * 3600)
        
        # Statistics (thread-safe)
        self.uploaded_bytes = 0
        self.failed_uploads = 0
        self.successful_uploads = 0
        self.stats_lock = Lock()
        self.start_time = None
        self.stop_event = Event()
        
    def test_connection(self):
        """Test connection to server before starting"""
        print("Testing connection to server...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.target_host, self.target_port))
            sock.close()
            print(f"✓ Connection successful to {self.target_host}:{self.target_port}\n")
            return True
        except socket.gaierror:
            print(f"✗ Error: Cannot resolve hostname '{self.target_host}'")
            return False
        except socket.timeout:
            print(f"✗ Error: Connection timeout to {self.target_host}:{self.target_port}")
            return False
        except ConnectionRefusedError:
            print(f"✗ Error: Connection refused. Is the server running on port {self.target_port}?")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def generate_random_data(self, size):
        """Generate random data for upload"""
        # Use faster method for large data generation
        return bytearray(random.getrandbits(8) for _ in range(size))
    
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
        with self.stats_lock:
            uploaded = self.uploaded_bytes
            success = self.successful_uploads
            failed = self.failed_uploads
        
        progress = (uploaded / self.total_bytes) * 100 if not self.continuous else 0
        speed = self.calculate_speed(uploaded, elapsed)
        
        if self.continuous:
            status = (f"Uploaded: {self.format_bytes(uploaded)} | "
                     f"Speed: {speed} | "
                     f"Success: {success} | Failed: {failed} | "
                     f"Time: {int(elapsed)}s")
        else:
            status = (f"Progress: {progress:.1f}% | "
                     f"Uploaded: {self.format_bytes(uploaded)}/{self.format_bytes(self.total_bytes)} | "
                     f"Speed: {speed} | "
                     f"Success: {success} | Failed: {failed}")
        
        print(f"\r{status}", end='', flush=True)
    
    def send_data(self, data):
        """Send data to server (HTTP POST)"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.target_host, self.target_port))
            
            # Build HTTP POST request
            content_length = len(data)
            headers = (
                f"POST /upload HTTP/1.1\r\n"
                f"Host: {self.target_host}\r\n"
                f"Content-Length: {content_length}\r\n"
                f"Content-Type: application/octet-stream\r\n"
                f"Connection: keep-alive\r\n"
                f"\r\n"
            ).encode()
            
            # Send headers and data
            sock.sendall(headers)
            sock.sendall(data)
            
            # Try to read response (optional)
            try:
                response = sock.recv(1024)
            except:
                pass
            
            return True
            
        except Exception as e:
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def upload_worker(self, worker_id):
        """Worker thread for uploading chunks"""
        while not self.stop_event.is_set():
            # Check if we should stop
            if not self.continuous:
                with self.stats_lock:
                    if self.uploaded_bytes >= self.total_bytes:
                        break
            
            # Generate and upload data
            data = self.generate_random_data(self.chunk_size_bytes)
            success = self.send_data(data)
            
            with self.stats_lock:
                if success:
                    self.uploaded_bytes += len(data)
                    self.successful_uploads += 1
                else:
                    self.failed_uploads += 1
            
            # Small delay to prevent overwhelming the connection
            time.sleep(0.01)
    
    def speed_controller(self):
        """Control upload speed to match target"""
        last_check = time.time()
        last_bytes = 0
        
        while not self.stop_event.is_set():
            time.sleep(1)
            
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            with self.stats_lock:
                current_bytes = self.uploaded_bytes
            
            # Calculate expected bytes at this point
            expected_bytes = self.bytes_per_second * elapsed
            
            # If we're going too fast, slow down all threads
            if current_bytes > expected_bytes * 1.1:
                time.sleep(0.5)
            
            # Update progress display
            self.print_progress()
    
    def run(self):
        """Run parallel fake upload"""
        # Test connection first
        if not self.test_connection():
            print("\nFailed to connect to server. Please check:")
            print(f"  1. Is the server running? (python dummy_server.py -p {self.target_port})")
            print(f"  2. Is the hostname correct? ({self.target_host})")
            print(f"  3. Is the port correct? ({self.target_port})")
            print(f"  4. Is there a firewall blocking the connection?")
            return
        
        print(f"{'='*70}")
        print(f"Starting Parallel Fake Upload")
        print(f"{'='*70}")
        print(f"Target: {self.target_host}:{self.target_port}")
        print(f"Goal: {self.daily_gb} GB in {self.duration_hours} hours")
        print(f"Target Speed: {self.format_bytes(self.bytes_per_second)}/s")
        print(f"Chunk Size: {self.chunk_size_mb} MB")
        print(f"Parallel Threads: {self.num_threads}")
        print(f"Mode: {'Continuous' if self.continuous else 'Limited'}")
        print(f"{'='*70}\n")
        print("Press Ctrl+C to stop\n")
        
        self.start_time = time.time()
        end_time = self.start_time + (self.duration_hours * 3600)
        
        # Start worker threads
        workers = []
        for i in range(self.num_threads):
            worker = Thread(target=self.upload_worker, args=(i,), daemon=True)
            worker.start()
            workers.append(worker)
        
        # Start speed controller
        controller = Thread(target=self.speed_controller, daemon=True)
        controller.start()
        
        try:
            # Wait for completion or timeout
            while not self.stop_event.is_set():
                if not self.continuous:
                    # Check if target reached
                    with self.stats_lock:
                        if self.uploaded_bytes >= self.total_bytes:
                            break
                    
                    # Check if time expired
                    if time.time() >= end_time:
                        break
                
                time.sleep(0.5)
            
            # Stop all threads
            self.stop_event.set()
            
            # Wait for workers to finish
            for worker in workers:
                worker.join(timeout=2)
            
            # Display final result
            print("\n")
            print(f"\n{'='*70}")
            print("Upload Completed!")
            print(f"{'='*70}")
            total_time = time.time() - self.start_time
            
            with self.stats_lock:
                final_bytes = self.uploaded_bytes
                success = self.successful_uploads
                failed = self.failed_uploads
            
            avg_speed = self.calculate_speed(final_bytes, total_time)
            success_rate = (success / (success + failed) * 100) if (success + failed) > 0 else 0
            
            print(f"Total Uploaded: {self.format_bytes(final_bytes)}")
            print(f"Total Time: {int(total_time)} seconds ({total_time/3600:.2f} hours)")
            print(f"Average Speed: {avg_speed}")
            print(f"Successful Uploads: {success}")
            print(f"Failed Uploads: {failed}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"{'='*70}\n")
            
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            self.stop_event.set()
            for worker in workers:
                worker.join(timeout=1)
    
    def stop(self):
        """Stop upload"""
        self.stop_event.set()


def signal_handler(sig, frame):
    """Handle Ctrl+C signal"""
    print("\n\nReceived stop signal...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Parallel Fake Upload Generator - Network Traffic Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  
  # Upload 400GB in 24 hours with 4 parallel threads:
  python fake_upload.py -g 400
  
  # Upload 100GB in 12 hours with 8 parallel threads:
  python fake_upload.py -g 100 -d 12 -t 8
  
  # Continuous upload with 6 threads:
  python fake_upload.py -g 50 -c -t 6
  
  # Upload to specific server:
  python fake_upload.py -g 200 -H example.com -p 8080 -t 4
  
  # High-speed upload with small chunks and many threads:
  python fake_upload.py -g 500 -s 5 -t 16
        """
    )
    
    parser.add_argument('-g', '--gigabytes', type=float, required=True,
                        help='Gigabytes to upload (example: 400)')
    
    parser.add_argument('-H', '--host', type=str, default='localhost',
                        help='Target server address (default: localhost)')
    
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help='Server port (default: 8080)')
    
    parser.add_argument('-s', '--chunk-size', type=int, default=10,
                        help='Chunk size in megabytes (default: 10)')
    
    parser.add_argument('-d', '--duration', type=float, default=24,
                        help='Upload duration in hours (default: 24)')
    
    parser.add_argument('-t', '--threads', type=int, default=4,
                        help='Number of parallel upload threads (default: 4)')
    
    parser.add_argument('-c', '--continuous', action='store_true',
                        help='Continuous upload without limit')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.threads < 1 or args.threads > 100:
        print("Error: Number of threads must be between 1 and 100")
        sys.exit(1)
    
    if args.chunk_size < 1 or args.chunk_size > 100:
        print("Error: Chunk size must be between 1 and 100 MB")
        sys.exit(1)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and run uploader
    uploader = ParallelUploader(
        target_host=args.host,
        target_port=args.port,
        daily_gb=args.gigabytes,
        chunk_size_mb=args.chunk_size,
        continuous=args.continuous,
        duration_hours=args.duration,
        threads=args.threads
    )
    
    try:
        uploader.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
