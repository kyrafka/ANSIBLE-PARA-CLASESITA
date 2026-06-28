import json,urllib.request
API='http://localhost/zabbix/api_jsonrpc.php'
payload={'jsonrpc':'2.0','method':'user.login','params':{'username':'Admin','password':'zabbix'},'id':1}
req=urllib.request.Request(API,json.dumps(payload).encode(),{'Content-Type':'application/json-rpc'})
with urllib.request.urlopen(req) as r: token=json.loads(r.read())['result']

def api(m,p,i):
    payload={'jsonrpc':'2.0','method':m,'params':p,'auth':token,'id':i}
    req=urllib.request.Request(API,json.dumps(payload).encode(),{'Content-Type':'application/json-rpc'})
    with urllib.request.urlopen(req) as r: return json.loads(r.read())

print("=== Interfaces de vm-monitor01 (hostid 10084) ===")
r=api('hostinterface.get',{'hostids':['10084']},10)
for i in r.get('result',[]):
    print(f"  interfaceid: {i['interfaceid']}, ip: {i['ip']}, main: {i['main']}, type: {i['type']}")