#!/bin/bash
API="http://192.168.17.11/zabbix/api_jsonrpc.php"

echo "=== Obteniendo token ==="
TOKEN=$(curl -s -X POST "$API" \
  -H "Content-Type: application/json-rpc" \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"username":"Admin","password":"zabbix"},"id":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',''))")

echo "Token: $TOKEN"

echo "=== Buscando actions ==="
curl -s -X POST "$API" \
  -H "Content-Type: application/json-rpc" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"action.get\",\"params\":{\"output\":[\"actionid\",\"name\",\"status\"]},\"auth\":\"$TOKEN\",\"id\":2}" \
  | python3 -m json.tool