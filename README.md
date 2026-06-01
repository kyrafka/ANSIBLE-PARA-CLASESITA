# Linux Core 1 & Core 2 — Infraestructura Ansible (HA OSPF + Keepalived)

> **Autogenerado** con Ansible para Ubuntu 24 Server (netplan) + OSPF + Keepalived HA + Aprovisionamiento de Servicios

---

```
                                    +---------+        +---------+
          pfSense (Trunk VLANs) ---->|  Core 1 |<------>|  Core 2 |
                                     |  MASTER |< OS  >|  BACKUP |
                                     +----+----+        +----+----+
                                          |                  |
                 Interlink 10.0.0.0/30 ------+                  |
                                                                      |
                                     +--------------------+         |
                                     | Switches de Acceso |<---------+
                                     +--------------------+
                                              |
                                              |
              +-------------------------------+-------------------------------+
              |                               |                               |
        vm-web01 (VLAN 10,30)        vm-services01 (VLAN 30)      vm-voip01 (VLAN 30,50)
        vm-storage01 (VLAN 30,40)    vm-monitor01 (VLAN 70)       vm-docker01 (VLAN 30)
```

---

## 1. Qué contiene este repo

Esta colección automatiza:

### Infraestructura de Red
| Componente | Propósito | Paquete |
| --- | --- | --- |
| **VLANs 802.1Q** | Trunk con pfSense y switches de acceso | `vlan` + `bridge-utils` |
| **Bridges** | Bridging por VLAN para tráfico L2/L3 | `bridge-utils` + netplan |
| **OSPF** | Routing dinámico entre Core 1 y Core 2 | `frr` |
| **Keepalived** | VIPs flotantes por VLAN (HA) | `keepalived` |
| **Netplan** | Gestión persistente de interfaces | `netplan.io` |
| **iptables** | NAT/masquerade (base) | `iptables-persistent` |

### Aprovisionamiento de Servicios Ubuntu
| VM | Servicios | VLANs |
| --- | --- | --- |
| **vm-services01** | Samba + iRedMail | 30 |
| **vm-web01** | Nginx + HAProxy + PostgreSQL | 10, 30 |
| **vm-voip01** | FreePBX | 30, 50 |
| **vm-monitor01** | Zabbix + Grafana | 70 |
| **vm-storage01** | NFS + PBS + rclone | 30, 40 |
| **vm-docker01** | Docker + Docker Compose | 30 |

---

## 2. Estructura del repositorio

```
ANSIBLE-PARA-CLASESITA/
├── ansible.cfg                           # Configuración Ansible (local execution)
├── core1_setup.yml                       # Playbook para Core 1 (MASTER, prio 200)
├── core2_setup.yml                       # Playbook para Core 2 (BACKUP, prio 100)
│
├── vars/
│   └── main.yml                          # CONFIGURACIÓN PRINCIPAL: VLANs, IPs, NICs
│
├── roles/linux_core/
│   ├── defaults/main.yml                 # Valores por defecto del role
│   ├── handlers/main.yml                 # Handlers (reload de servicios)
│   ├── tasks/
│   │   ├── main.yml                      # Orquestador (importa los demás)
│   │   ├── prerequisites.yml             # Paquetes, módulos kernel, sysctl
│   │   ├── networking.yml                # Netplan (bridges, VLANs, IPs)
│   │   ├── frr.yml                       # Configuración OSPF
│   │   └── keepalived.yml                # Configuración HA VIPs
│   └── templates/
│       ├── netplan_config.yaml.j2        # Plantilla de red (bridges, VLANs, IPs)
│       ├── frr.conf.j2                   # Configuración OSPF
│       ├── daemons.j2                    # Daemons de FRR (activa ospfd)
│       └── keepalived.conf.j2            # Configuración VRRP por VLAN
│
├── playbooks/                            # Playbooks de aprovisionamiento de servicios
│   ├── deploy_all.yml                    # Playbook maestro (incluye todos)
│   ├── vm-services01.yml                 # Samba + iRedMail
│   ├── vm-web01.yml                      # Nginx + HAProxy + PostgreSQL
│   ├── vm-voip01.yml                     # FreePBX + Asterisk
│   ├── vm-monitor01.yml                  # Zabbix + Grafana
│   ├── vm-storage01.yml                  # NFS + PBS + rclone
│   └── vm-docker01.yml                   # Docker + Docker Compose
│
├── inventario/
│   └── hosts.yml                         # Inventario de VMs y sus VLANs/IP
│
├── docs/
│   ├── esxi_connection.yml               # Credenciales y conexión ESXi
│   └── topologia_vms.md                  # Documentación gráfica de VMs
│
└── README.md                             # Este archivo
```

---

## 3. Configuración crítica — `vars/main.yml`

### 3.1 Nombres de interfaces (adaptar a tu ESXi)

```yaml
nic_wan: "eth0"          # Trunk con pfSense
nic_lan: "eth1"          # Trunk con switches de acceso
nic_interlink: "eth2"    # Interlink Core1 ↔ Core2
```

### 3.2 VLANs definidas en tu laboratorio

| VLAN ID | Nombre | Subred | VMs associadas |
| --- | --- | --- | --- |
| 10 | DMZ | 10.0.10.0/24 | vm-web01 |
| 30 | Virtualización | 10.0.30.0/24 | vm-services01, vm-web01, vm-voip01, vm-storage01, vm-docker01 |
| 40 | Storage | 10.0.40.0/24 | vm-storage01 |
| 50 | VoIP | 10.0.50.0/24 | vm-voip01 |
| 60 | Gestión | 10.0.60.0/24 | vm-dc01 (Windows — **NO automatizar**) |
| 70 | Monitoreo | 10.0.70.0/24 | vm-monitor01 |

```yaml
vlans:
  - id: 10
    name: "dmz"
    subnet: "10.0.10.0/24"
    core1_ip: "10.0.10.2/24"
    core2_ip: "10.0.10.3/24"
    vip: "10.0.10.1/24"
    vrid: 10
  - id: 30
    name: "virtualizacion"
    subnet: "10.0.30.0/24"
    core1_ip: "10.0.30.2/24"
    core2_ip: "10.0.30.3/24"
    vip: "10.0.30.1/24"
    vrid: 30
  # ... ver archivo completo
```

---

## 4. ESXi — Conexión

| Parámetro | Valor |
| --- | --- |
| URL | `https://168.121.48.254:10112/ui/#/host/vms` |
| Usuario | `root` |
| Contraseña | `qwe123$` |

---

## 5. Ejecución

### 5.1 Core Routers (Keepalived HA)

```bash
# En Core 1
sudo ansible-playbook core1_setup.yml

# En Core 2
sudo ansible-playbook core2_setup.yml
```

### 5.2 Servicios Ubuntu (usando inventario)

```bash
# Desplegar todos los servicios
ansible-playbook -i inventario/hosts.yml playbooks/deploy_all.yml

# O uno por uno:
ansible-playbook -i inventario/hosts.yml playbooks/vm-web01.yml
ansible-playbook -i inventario/hosts.yml playbooks/vm-docker01.yml
# ... etc
```

---

## 6. Verificación post-instalación

### Netplan / interfaces
```bash
ip -br a
bridge link show
```

### OSPF (FRR)
```bash
sudo vtysh
show ip ospf neighbor
show ip ospf database
show ip ospf route
```

### Keepalived (HA)
```bash
sudo systemctl status keepalived
ip addr show | grep "inet.*br-vlan"
```

---

## 7. Troubleshooting

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `Fatal: interface X no existe` | NICs con nombres diferentes en ESXi | Editar `vars/main.yml` → `nic_wan`, `nic_lan`, `nic_interlink` |
| `netplan generate` falla | Sintaxis YAML incorrecta | Verificar indentación en `templates/netplan_config.yaml.j2` |
| OSPF no forma adjacencia | No hay conectividad interlink | Ping entre Core 1 (10.0.0.1) y Core 2 (10.0.0.2) |
| VIPs duplicados | Ambos cores en MASTER | Verificar conectividad interlink. Revisar logs de keepalived |
| Zabbix no arranca | Base de datos vacía o sin privilegios | Verificar MariaDB, usuario y contraseña en el playbook |
| Docker no encuentra cli | Plugin no instalado correctamente | Reinstalar `docker-compose-plugin` |

---

## 8. Changelog

| Fecha | Fix / Feature | Archivo |
| --- | --- | --- |
| 2026-05-31 | Fixed `failed_when` con OR en NIC check | `tasks/prerequisites.yml` |
| 2026-05-31 | Modularización en role `linux_core` | Todo el árbol `roles/` |
| 2026-05-31 | VLANs ajustadas a topología real del laboratorio | `vars/main.yml` |
| 2026-05-31 | Playbooks de aprovisionamiento de servicios Ubuntu creados | `playbooks/*.yml` |
| 2026-05-31 | Inventario de VMs y conexión ESXi documentados | `inventario/`, `docs/` |

---

## 9. Licencia

MIT / Open Source — adaptado al gusto. PRs bienvenidos.
