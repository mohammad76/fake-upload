#!/bin/bash
# Quick launcher for local server + upload
# راه‌انداز سریع برای سرور محلی + آپلود

echo "=================================="
echo "🚀 Fake Upload - Local Setup"
echo "=================================="
echo ""

# Default values
GB=${1:-400}
THREADS=${2:-8}
PORT=8080

echo "📊 Configuration:"
echo "  - Upload: ${GB} GB"
echo "  - Threads: ${THREADS}"
echo "  - Port: ${PORT}"
echo ""

# Check if server is already running
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✓ Server already running on port ${PORT}"
else
    echo "🔄 Starting server on port ${PORT}..."
    python3 dummy_server.py -p ${PORT} &
    SERVER_PID=$!
    sleep 2
    
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "✓ Server started successfully (PID: ${SERVER_PID})"
    else
        echo "✗ Failed to start server"
        exit 1
    fi
fi

echo ""
echo "🌐 Web interface: http://localhost:${PORT}"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================="
echo ""

# Wait a moment for server to be ready
sleep 1

# Start upload
python3 fake_upload.py -g ${GB} -p ${PORT} -t ${THREADS}

echo ""
echo "Upload finished!"
