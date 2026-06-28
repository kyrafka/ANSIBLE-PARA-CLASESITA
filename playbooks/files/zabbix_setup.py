#!/usr/bin/env python3
"""
zabbix_setup.py — Configura Zabbix 7 completo
Uso: python3 zabbix_setup.py <api_url> <user> <pass> <email>
"""
import sys
import json
import urllib.request

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


def upsert_script(name, command, description, scope=1):
    existing = api_call("script.get", {"filter": {"name": [name]}}, token)
    if existing:
        sid = existing[0]["scriptid"]
        api_call("script.update", {"scriptid": sid, "command": command}, token)
        print(f"  Actualizado: {name} (id:{sid})")
        return sid
    else:
        result = api_call("script.create", {
            "name": name,
            "command": command,
            "execute_on": 0,
            "type": 0,
            "scope": scope,
            "description": description
        }, token)
        sid = result["scriptids"][0]
        print(f"  Creado: {name} (id:{sid})")
        return sid


def upsert_trigger(description, expression, priority, tags, hostid=None):
    if hostid:
        existing = api_call("trigger.get", {"filter": {"description": [description]}, "hostids": [hostid]}, token)
    else:
        existing = api_call("trigger.get", {"filter": {"description": [description]}}, token)
    if existing:
        tid = existing[0]["triggerid"]
        api_call("trigger.delete", [tid], token)
        print(f"  Eliminada previa trigger: {description[:50]}")
    result = api_call("trigger.create", {
        "description": description,
        "expression": expression,
        "priority": priority,
        "manual_close": 1,
        "tags": tags
    }, token)
    print(f"  Creado trigger: {description[:50]} (id:{result['triggerids'][0]})")
    return result['triggerids'][0]


def upsert_action(name, params):
    existing = api_call("action.get", {"filter": {"name": [name]}, "output": ["actionid"]}, token)
    if existing:
        aid = existing[0]["actionid"]
        api_call("action.delete", [aid], token)
        print(f"  Eliminada previa: {name}")
    result = api_call("action.create", params, token)
    print(f"  Creada: {name} (id:{result['actionids'][0]})")


# =========================================================================
# 1. Autenticar
# =========================================================================
print("=== AUTENTICACION ===")
token = api_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
print(f"TOKEN OK: {token[:20]}...")


# =========================================================================
# 2. Scripts
# =========================================================================
print("\n=== SCRIPTS ===")

poweron_sid = upsert_script(
    "AXIOM: PowerOn VM en ESXi",
    "sudo /usr/local/bin/vm-poweron.sh {HOST.NAME}",
    "Enciende la VM en ESXi via govc"
)

upsert_script(
    "AXIOM: Restart Service via SSH",
    "sudo /usr/local/bin/service-restart.sh {HOST.CONN} {EVENT.TAGS.__service}",
    "Reinicia servicio caido en host remoto via SSH"
)

# Script manual para ejecutar desde la UI de Zabbix
upsert_script(
    "AXIOM: PowerOn VM (manual)",
    "sudo /usr/local/bin/vm-poweron.sh {HOST.NAME}",
    "Encender VM manualmente desde Zabbix UI",
    scope=2  # scope=2 = manual host action (visible en UI)
)

upsert_script(
    "AXIOM: Ver servicios del host",
    "ssh -o StrictHostKeyChecking=no sysadmin@{HOST.CONN} 'systemctl list-units --type=service --state=running'",
    "Lista servicios corriendo en el host",
    scope=2
)

restart_sid = upsert_script(
    "AXIOM: Restart Service",
    "sudo /usr/local/bin/service-restart.sh {HOST.CONN} {EVENT.TAGS.__service}",
    "Reinicia servicio caido en host remoto via SSH"
)


# =========================================================================
# 3. Media type Email
# =========================================================================
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
    print(f"  Creado (id:{mt_id})")


# =========================================================================
# 4. Usuario Admin — asignar email
# =========================================================================
print("\n=== USUARIO ADMIN ===")
users = api_call("user.get", {"filter": {"username": ["Admin"]}, "output": ["userid"]}, token)
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
print(f"  Email: {ALERT_EMAIL} → Admin")


# =========================================================================
# 5. Actions
# =========================================================================
print("\n=== ACTIONS ===")

# Action 1: VM apagada → PowerOn ESXi
# severity >= Average cubre: agente no disponible (Average) y cualquier problema grave (High+)
upsert_action("AXIOM: Auto PowerOn VM en ESXi", {
    "name": "AXIOM: Auto PowerOn VM en ESXi",
    "eventsource": 0,
    "status": 0,
    "esc_period": "60",
    "filter": {
        "evaltype": 0,
        "conditions": [{"conditiontype": 4, "operator": 5, "value": "2"}]
    },
    "operations": [{
        "operationtype": 1,
        "esc_period": "0",
        "esc_step_from": 1,
        "esc_step_to": 1,
        "opcommand": {"scriptid": poweron_sid},
        "opcommand_hst": [{"hostid": "0"}]
    }]
})
upsert_action("AXIOM: Notificacion Email Problemas", {
    "name": "AXIOM: Notificacion Email Problemas",
    "eventsource": 0,
    "status": 0,
    "esc_period": "1h",
    "filter": {
        "evaltype": 0,
        "conditions": [{"conditiontype": 4, "operator": 5, "value": "2"}]
    },
    "operations": [{
        "operationtype": 0,
        "esc_period": "0",
        "esc_step_from": 1,
        "esc_step_to": 1,
        "opmessage": {"default_msg": 1, "mediatypeid": mt_id},
        "opmessage_usr": [{"userid": user_id}]
    }],
    "recovery_operations": [{
        "operationtype": 0,
        "opmessage": {"default_msg": 1, "mediatypeid": mt_id},
        "opmessage_usr": [{"userid": user_id}]
    }]
})

# Action: Servicio caido → Restart via SSH
upsert_action("AXIOM: Auto Restart Servicio Caido", {
    "name": "AXIOM: Auto Restart Servicio Caido",
    "eventsource": 0,
    "status": 0,
    "esc_period": "60",
    "filter": {
        "evaltype": 0,
        "conditions": [
            {"conditiontype": 4, "operator": 5, "value": "2"}
        ]
    },
    "operations": [{
        "operationtype": 1,
        "esc_period": "0",
        "esc_step_from": 1,
        "esc_step_to": 1,
        "opcommand": {"scriptid": restart_sid},
        "opcommand_hst": [{"hostid": "0"}]
    }],
    "recovery_operations": [{
        "operationtype": 0,
        "opmessage": {"default_msg": 1, "mediatypeid": mt_id},
        "opmessage_usr": [{"userid": user_id}]
    }]
})


# =========================================================================
# 6. Triggers de servicios por host
# =========================================================================
print("\n=== TRIGGERS DE SERVICIOS ===")

# Mapa de servicios por host (según inventario)
# Mapa de servicios por host (según playbooks de cada VM)
HOST_SERVICES = {
    "vm-web01":      ["nginx", "mariadb"],
    "vm-services01": ["postfix", "dovecot", "mysql", "apache2"],
    "vm-voip01":     ["asterisk"],
    "vm-monitor01":  ["zabbix_server", "grafana-server", "apache2", "mariadb"],
    "vm-storage01":  ["smbd", "nfsd"],
    "vm-docker01":   ["dockerd", "mysql", "nginx"],
    "vm-dc01":       ["samba-ad-dc", "named", "isc-dhcp-server"],
}

# Obtener hosts registrados
all_hosts = api_call("host.get", {"output": ["hostid", "name"]}, token)
hosts_map = {h["name"]: h["hostid"] for h in all_hosts}

# Trigger de agente caido con deteccion en 60s en cada host
print("\n=== TRIGGERS AGENT DOWN (60s) ===")
for h in all_hosts:
    hname = h["name"]
    hid = h["hostid"]
    tname = f"{hname}: Agent no responde — PowerOn ESXi"
    existing = api_call("trigger.get", {"filter": {"description": tname}, "hostids": [hid]}, token)
    if existing:
        try:
            api_call("trigger.delete", [existing[0]["triggerid"]], token)
            print(f"  Eliminada previa: {tname}")
        except:
            pass
    try:
        api_call("trigger.create", {
            "description": tname,
            "expression": f"nodata(/{hname}/agent.ping,60s)=1",
            "priority": 4,
            "manual_close": 1,
            "tags": [{"tag": "scope", "value": "availability"}, {"tag": "auto_recovery", "value": "poweron"}]
        }, token)
        print(f"  Creado: {tname}")
    except Exception as e:
        print(f"  ERROR {hname}: {e}")

for hostname, services in HOST_SERVICES.items():
    hostid = hosts_map.get(hostname)
    if not hostid:
        print(f"  SKIP: {hostname} no encontrado en Zabbix")
        continue

    for svc in services:
        item_key = f"proc.num[{svc}]"
        trigger_name = f"{hostname}: Servicio {svc} caido"

        # Obtener interfaz del host
        ifaces = api_call("hostinterface.get", {"hostids": [hostid]}, token)
        if not ifaces:
            print(f"  SKIP {hostname}/{svc}: sin interfaz")
            continue
        ifaceid = ifaces[0]["interfaceid"]

        # Crear/actualizar item - eliminar primero si existe
        existing_item = api_call("item.get", {
            "hostids": [hostid],
            "filter": {"key_": item_key}
        }, token)

        if existing_item:
            try:
                api_call("item.delete", [existing_item[0]["itemid"]], token)
                print(f"  Item eliminado previa: {hostname}/{item_key}")
            except:
                pass

        try:
            api_call("item.create", {
                "hostid": hostid,
                "name": f"Procesos {svc} corriendo",
                "key_": item_key,
                "type": 0,          # Zabbix agent
                "value_type": 3,    # numeric unsigned
                "interfaceid": ifaceid,
                "delay": "30s",
                "history": "7d",
                "trends": "30d",
                "tags": [{"tag": "service", "value": svc}]
            }, token)
            print(f"  Item creado: {item_key} en {hostname}")
        except Exception as e:
            print(f"  ERROR item {hostname}/{svc}: {e}")
            continue

        # Crear trigger (eliminar primero si existe)
        existing_trigger = api_call("trigger.get", {
            "filter": {"description": trigger_name},
            "hostids": [hostid]
        }, token)
        if existing_trigger:
            print(f"  Existe trigger: {trigger_name}")
            continue

        try:
            api_call("trigger.delete", [existing_trigger[0]["triggerid"]], token)
            print(f"  Eliminada previa trigger: {trigger_name}")
        except:
            pass

        try:
            api_call("trigger.create", {
                "description": trigger_name,
                "expression": f"last(/{hostname}/{item_key})<1",
                "priority": 3,
                "manual_close": 1,
                "tags": [
                    {"tag": "service", "value": svc},
                    {"tag": "__service", "value": svc},
                    {"tag": "scope", "value": "availability"}
                ]
            }, token)
            print(f"  Trigger creado: {trigger_name}")
        except Exception as e:
            print(f"  ERROR trigger {hostname}/{svc}: {e}")


# =========================================================================
# 7. Resumen
# =========================================================================
print("\n=== ACTIONS ACTIVAS ===")
all_actions = api_call("action.get", {
    "output": ["name", "status"],
    "filter": {"eventsource": 0}
}, token)
print(f"Total: {len(all_actions)}")
for a in all_actions:
    estado = "ACTIVA" if a["status"] == "0" else "DESACT"
    print(f"  [{estado}] {a['name']}")

print("\n=== SCRIPTS REGISTRADOS ===")
all_scripts = api_call("script.get", {"output": ["name", "command"]}, token)
for s in all_scripts:
    print(f"  {s['name']}")

print("\nOK — Configuracion completada")
