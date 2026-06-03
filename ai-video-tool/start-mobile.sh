#!/usr/bin/env bash
# Quick-start for local mobile testing.
# Usage: ./start-mobile.sh  (run from the ai-video-tool directory)
set -e

cd "$(dirname "$0")"

if [ ! -f ".env" ]; then
  if [ -f "backend/.env.sample" ]; then
    cp backend/.env.sample .env
    echo "⚠️  Created .env from sample — add your ANTHROPIC_API_KEY before continuing."
    exit 1
  fi
fi

# Detect local IP for the QR / mobile URL
LOCAL_IP=$(python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
    s.close()
except:
    print('127.0.0.1')
")

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║          AI Video Creator — Mobile           ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Local:   http://localhost:8000              ║"
echo "║  Network: http://${LOCAL_IP}:8000              ║"
echo "║                                              ║"
echo "║  Scan the QR code in the app header (📱)    ║"
echo "║  to open on your phone.                     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

docker compose up --build
