#!/bin/bash
# Server cleanup script - Run this on your deployment server

echo "🧹 Starting server cleanup..."

# 1. Docker cleanup (most important)
echo "📦 Cleaning Docker..."
docker system prune -a --volumes -f
docker builder prune -a -f

# 2. Remove old project
echo "🗑️  Removing old project..."
cd /home/ubuntu
rm -rf mobile_programming_server

# 3. Clean system caches
echo "💾 Cleaning system caches..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y

# 4. Clean logs
echo "📋 Cleaning old logs..."
sudo journalctl --vacuum-time=1d
sudo find /var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true

# 5. Clean tmp files
echo "🗂️  Cleaning temp files..."
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# 6. Show disk usage
echo ""
echo "✅ Cleanup complete! Current disk usage:"
df -h /

echo ""
echo "📊 Space usage by directory:"
du -sh /var/lib/docker 2>/dev/null || echo "/var/lib/docker not found"
du -sh /home/ubuntu/* 2>/dev/null | sort -h || true

echo ""
echo "🚀 Ready to clone and deploy!"
echo "Run: git clone https://github.com/alswns/mobile_programming_server.git"
