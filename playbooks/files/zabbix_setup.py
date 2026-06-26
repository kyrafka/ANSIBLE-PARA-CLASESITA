#!/usr/bin/env python3
"""
zabbix_setup.py — Configura actions, scripts y notificaciones en Zabbix 7
Uso: python3 zabbix_setup.py <api_url> <user> <pass> <email>
"""
import sys
import json
import urllib.request
import urllib.error

API = sys.argv[1]
ZABBIX_USER = sys.argv[2]
ZABBIX_PASS = sys.argv[3]
ALERT_EMAIL = sys.argv[4]


def api_call(method, params, token=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if token:
        payload["auth"] = token
    data = json.dumps(payload).encode()
    req = urllib.request.Request(API, data, {"Content-Type": "application/json-rpc"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if "error" in result:
        raise Exception(f"{method} error: {result['error']['data']}")
    return result["result"]


# 1. Autenticar
print("=== AUTENTICACION ===")
token = api_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
print(f"TOKEN OK: {token[:20]}...")


# 2. Registrar scripts en Zabbix
print("\n=== SCRIPTS ===")

def upsert_script(name, command, description):
    existing = api_call("script.get", {"filter": {"name": [name]}}, token)
    if existing:
        sid = existing[0]["scriptid"]
        api_call("script.update", {"scriptid": sid, "command": command}, token)
        print(f"  Actualizado: {name} (id:{sid})")
    else:
        result = api_call("script.create", {
            "name": name,
            "command": command,
            "execute_on": 0,
            "type": 0,
            "scope": 1,
            "description": description
        }, token)
        print(f"  Creado: {name} (id:{result['scriptids'][0]})")

upsert_script(
    "AXIOM: PowerOn VM en ESXi",
    "/usr/local/bin/vm-poweron.sh {HOST.NAME}",
    "Enciende la VM en ESXi usando el nombre del host Zabbix"
)
upsert_script(
    "AXIOM: Restart Service via SSH",
    "/usr/local/bin/service-restart.sh {HOST.CONN} {EVENT.TAGS.__service}",
    "Reinicia el servicio caido en el host remoto via SSH"
)


# 3. Configurar media type Email
print("\n=== MEDIA TYPE EMAIL ===")
mt_list = api_call("mediatype.get", {"filter": {"name": ["Email"]}}, token)
if mt_list:
    mt_id = mt_list[0]["mediatypeid"]
    print(f"  Email ya existe (id:{mt_id})")
else:
    result = api_call("mediatype.create", {
        "type": 0,
        "name": "Email",
        "smtp_server": "localhost",
        "smtp_port": 25,
        "smtp_helo": "zabbix.local",
        "smtp_email": "zabbix@zabbix.local"
    }, token)
    mt_id = result["mediatypeids"][0]
    print(f"  Creado Email media type (id:{mt_id})")


# 4. Asignar email al usuario Admin
print("\n=== USUARIO ADMIN ===")
users = api_call("user.get", {"filter": {"username": ["Admin"]}, "output": ["userid"]}, token)
if not users:
    print("  ERROR: Usuario Admin no encontrado")
    sys.exit(1)

user_id = users[0]["userid"]
api_call("user.update", {
    "userid": user_id,
    "medias": [{
        "mediatypeid": mt_id,
        "sendto": [ALERT_EMAIL],
        "active": 0,
        "severity": 63,
        "period": "1-7,00:00-24:00"
    }]
}, token)
print(f"  Email asignado a Admin: {ALERT_EMAIL}")


# 5. Crear/actualizar actions
print("\n=== ACTIONS ===")

def upsert_action(name, params):
    existing = api_call("action.get", {"filter": {"name": [name]}, "output": ["actionid"]}, token)
    if existing:
        aid = existing[0]["actionid"]
        api_call("action.delete", [aid], token)
        print(f"  Eliminada action previa: {name}")
    result = api_call("action.create", params, token)
    print(f"  Creada: {name} (id:{result['actionids'][0]})")


# Action: VM apagada → PowerOn ESXi
upsert_action("AXIOM: Auto PowerOn VM en ESXi", {
    "name": "AXIOM: Auto PowerOn VM en ESXi",
    "eventsource": 0,
    "status": 0,
    "esc_period": "2m",
    "filter": {
        "evaltype": 0,
        "conditions": [{
            "conditiontype": 16,
            "operator": 10,
            "value": "Agent no responde"
        }]
    },
    "operations": [{
        "operationtype": 1,
        "esc_period": "0",
        "esc_step_from": 1,
        "esc_step_to": 1,
        "opcommand": {
            "type": 0,
            "command": "/usr/local/bin/vm-poweron.sh {HOST.NAME}",
            "execute_on": 0
        },
        "opcommand_hst": [{"hostid": "0"}]
    }]
})

# Action: Notificacion email en problemas >= Warning
upsert_action("AXIOM: Notificacion Email Problemas", {
    "name": "AXIOM: Notificacion Email Problemas",
    "eventsource": 0,
    "status": 0,
    "esc_period": "1h",
    "filter": {
        "evaltype": 0,
        "conditions": [{
            "conditiontype": 4,
            "operator": 5,
            "value": "2"
        }]
    },
    "operations": [{
        "operationtype": 0,
        "esc_period": "0",
        "esc_step_from": 1,
        "esc_step_to": 1,
        "opmessage": {
            "default_msg": 1,
            "mediatypeid": mt_id
        },
        "opmessage_usr": [{"userid": user_id}]
    }],
    "recovery_operations": [{
        "operationtype": 0,
        "opmessage": {
            "default_msg": 1,
            "mediatypeid": mt_id
        },
        "opmessage_usr": [{"userid": user_id}]
    }]
})


# 6. Resumen final
print("\n=== ACTIONS ACTIVAS ===")
all_actions = api_call("action.get", {
    "output": ["name", "status"],
    "filter": {"eventsource": 0}
}, token)
print(f"Total: {len(all_actions)}")
for a in all_actions:
    estado = "ACTIVA" if a["status"] == "0" else "DESACT"
    print(f"  [{estado}] {a['name']}")

print("\nOK — Configuracion completada")
