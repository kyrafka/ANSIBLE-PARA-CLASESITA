#!/bin/bash
# probe_esxi.sh — Descubre el endpoint correcto de la API REST del ESXi
# Corre esto desde tu WSL/local que tenga acceso a la red del Cisco

ESXI="172.17.25.12"
USER="root"
PASS="qwe123\$"

echo "================================================"
echo "PROBE ESXi API — $ESXI"
echo "================================================"

echo ""
echo "--- Version ESXi ---"
curl -sk "https://$ESXI/sdk/vimServiceVersions.xml" | grep -E "version|namespace" | head -5

echo ""
echo "--- Test /api/session (ESXi 7+) ---"
R=$(curl -sk -o - -w "\nHTTP:%{http_code}" -X POST "https://$ESXI/api/session" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS")
echo "$R" | tail -1
TOKEN_V7=$(echo "$R" | head -1 | tr -d '"')
echo "Token: ${TOKEN_V7:0:30}..."

echo ""
echo "--- Test /rest/com/vmware/cis/session (ESXi 6.x) ---"
R=$(curl -sk -o - -w "\nHTTP:%{http_code}" -X POST "https://$ESXI/rest/com/vmware/cis/session" \
  -u "$USER:$PASS")
echo "$R" | tail -1
TOKEN_V6=$(echo "$R" | head -1 | python3 -c "import sys,json; print(json.load(sys.stdin).get('value',''))" 2>/dev/null)
echo "Token: ${TOKEN_V6:0:30}..."

echo ""
echo "--- Listar VMs con token v7 ---"
if [ -n "$TOKEN_V7" ] && [ "$TOKEN_V7" != "null" ]; then
  curl -sk "https://$ESXI/api/vcenter/vm" \
    -H "vmware-api-session-id: $TOKEN_V7" \
    | python3 -c "import sys,json; vms=json.load(sys.stdin); [print(f'  {v[\"name\"]} ({v[\"vm\"]}) — {v[\"power_state\"]}') for v in (vms if isinstance(vms,list) else [])]" 2>/dev/null
fi

echo ""
echo "--- Listar VMs con token v6 ---"
if [ -n "$TOKEN_V6" ] && [ "$TOKEN_V6" != "null" ]; then
  curl -sk "https://$ESXI/rest/vcenter/vm" \
    -H "vmware-api-session-id: $TOKEN_V6" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); vms=d.get('value',[]); [print(f'  {v[\"name\"]} ({v[\"vm\"]}) — {v[\"power_state\"]}') for v in vms]" 2>/dev/null
fi

echo ""
echo "================================================"
echo "DONE"
echo "================================================"
