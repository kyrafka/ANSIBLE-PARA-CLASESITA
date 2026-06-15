#!/bin/bash
echo "=== PROCESOS KEEPALIVED ==="
ps aux | grep keepalived | grep -v grep

echo ""
echo "=== ARCHIVOS EN /etc/keepalived/ ==="
ls -la /etc/keepalived/

echo ""
echo "=== CONFIG ACTUAL (state/priority/unicast) ==="
grep -E "state|priority|unicast" /etc/keepalived/keepalived.conf

echo ""
echo "=== ESTADO DE SERVICIO ==="
systemctl status keepalived --no-pager -l | head -20

echo ""
echo "=== ULTIMOS LOGS ==="
journalctl -u keepalived -n 15 --no-pager