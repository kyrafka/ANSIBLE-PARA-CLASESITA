# Ansible Multi-Site Infrastructure — Lima (HA), Arequipa y Trujillo

> **Automatizado con Ansible** para Ubuntu 24 Server + Netplan + HA (Keepalived VRRP) + OSPF + WireGuard VPN + DHCP/DNS distribuido

---

## Topología General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                    LIMA (Sede Maestra)                       │
│  ┌──────────────┐      ┌──────────────────────────────────────────────┐   │
│  │   pfSense HA  │      │         Core 1 (MASTER)  ←→  Core 2 (BACKUP)    │   │
│  │  (CARP VIPs)  │──────│  Keepalived VRRP Unicast  +  OSPF over FRR     │   │
│  └──────────────┘      │  10.0.0.1 ←→ 10.0.0.2 (Interlink)             │   │
│                        └──────────────────────────────────────────────┘   │
│                                       │                                      │
│   vm-services01: Samba AD, DNS, DHCP  │  vm-web01: Nginx, HAProxy, PostgreSQL│
│   vm-monitor01: Zabbix + Grafana      │  vm-docker01: Docker                 │
│   vm-dc01: Windows AD (manual)        │                                     │
│                                                                             │
│   WireGuard VPN Server ←──────────────────────────┐                         │
└────────────────────────────────────────────────────│─────────────────────────
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    │                                │                                │
             ┌──────┴───────┐              ┌────────┴────────┐
             │  AREQUIPA     │              │   TRUJILLO       │
             │               │              │                  │
             │ core-aqp      │              │ core-tru          │
             │ (DHCP local)  │              │ (DHCP local)      │
             │ (DNS forward) │              │ (DNS forward)     │
             │ (VPN client) │              │ (VPN client)      │
             │               │              │                   │
             │ 192.168.82.0/25│             │ 192.168.92.0/25   │
             │ 192.168.87.0/27│             │ 192.168.97.0/27   │
             └───────────────┘              └───────────────────┘
```

---

## Estructura del Repositorio

```
ANSIBLE-PARA-CLASESITA/
├── ansible.cfg                           # Configuración Ansible
├── core1_setup.yml                       # Core 1 MASTER (legacy, usar site.yml)
├── core2_setup.yml                       # Core 2 BACKUP (legacy, usar site.yml)
│
├── vars/
│   └── main.yml                          # VLANs, IPs, NICs compartidas
│
├── group_vars/
│   ├── all.yml                           # Variables globales (dominio, DNS, VPN)
│   ├── lima.yml                          # Variables específicas Lima
│   ├── arequipa.yml                      # Variables específicas Arequipa
│   └── trujillo.yml                      # Variables específicas Trujillo
│
├── roles/
│   ├── linux_core/                      # Core routers con HA (Keepalived + OSPF)
│   │   ├── tasks/
│   │   │   ├── main.yml                 # Prereq → Net → FRR → Keepalived
│   │   │   ├── prerequisites.yml
│   │   │   ├── networking.yml
│   │   │   ├── frr.yml
│   │   │   └── keepalived.yml
│   │   └── templates/
│   │       ├── netplan.yaml.j2
│   │       ├── keepalived.conf.j2
│   │       └── frr.conf.j2
│   │
│   └── sede_remota/                     # Sedes remotas (single core)
│       ├── tasks/
│       │   ├── main.yml                 # Prereq → Net → DHCP → DNS → VPN
│       │   ├── prerequisites.yml
│       │   ├── networking.yml
│       │   ├── dhcp.yml
│       │   ├── dns.yml
│       │   └── vpn_client.yml
│       ├── templates/
│       │   ├── netplan.yaml.j2
│       │   ├── dhcpd.conf.j2
│       │   ├── named.conf.options.j2
│       │   ├── named.conf.local.j2
│       │   └── wg0.conf.j2
│       └── handlers/main.yml
│
├── playbooks/
│   ├── site.yml                          # PLAYBOOK MAESTRO
│   ├── common/
│   │   ├── 00_prerequisites.yml          # Paquetes comunes
│   │   └── diagnostics.yml              # Verificación de red/DHCP/DNS/VPN
│   ├── lima/
│   │   ├── 00_core_ha.yml               # Core 1 + Core 2 en HA
│   │   └── 01_services.yml              # Samba AD, Web, Monitoreo
│   ├── arequipa/
│   │   └── 00_sede_base.yml             # Core + DHCP + DNS + VPN
│   └── trujillo/
│       └── 00_sede_base.yml             # Core + DHCP + DNS + VPN
│
├── inventario/
│   └── hosts.yml                         # Inventario por sitio
│
└── docs/
    ├── esxi_connection.yml
    └── topologia_vms.md
```

---

## Diseño por Sede

### Lima (Maestra — Alta Disponibilidad)
| Componente | Detalle |
|---|---|
| **Core 1** | MASTER Keepalived (prio 200), VRRP unicast |
| **Core 2** | BACKUP Keepalived (prio 100), VRRP unicast |
| **Interlink** | 10.0.0.1 ↔ 10.0.0.2 (OSPF + keepalived) |
| **VLANs** | 10, 20, 21, 30, 40, 50, 60, 70, 999 |
| **vm-services01** | Samba AD + DNS + DHCP (gestionado por Ansible) |
| **vm-dc01** | Windows AD — **manual, no automatizado** |
| **vm-web01** | Nginx + HAProxy + PostgreSQL |
| **vm-monitor01** | Zabbix + Grafana |
| **VPN** | WireGuard server (puerto 51820) |

### Arequipa (Sede Remota — Single Core)
| Componente | Detalle |
|---|---|
| **core-aqp** | Single core, sin HA |
| **VLANs locales** | VLAN 20 (usuarios), VLAN 60 (gestión) |
| **DHCP** | ISC DHCP server local (192.168.82.50-200, 192.168.87.10-20) |
| **DNS** | bind9 forwarder → Lima (192.168.16.4) |
| **VPN** | WireGuard client → Lima |
| **Subnets** | 192.168.82.0/25, 192.168.87.0/27 |

### Trujillo (Sede Remota — Single Core)
| Componente | Detalle |
|---|---|
| **core-tru** | Single core, sin HA |
| **VLANs locales** | VLAN 20 (usuarios), VLAN 60 (gestión) |
| **DHCP** | ISC DHCP server local (192.168.92.50-200, 192.168.97.10-20) |
| **DNS** | bind9 forwarder → Lima (192.168.16.4) |
| **VPN** | WireGuard client → Lima |
| **Subnets** | 192.168.92.0/25, 192.168.97.0/27 |

---

## Configuración de Interfaces (Cores Lima)

### Core 1
| Interfaz | Función |
|---|---|
| ens34 | Trunk 1 → pfSense Master |
| ens35 | Acceso directo |
| ens36 | Interlink → Core 2 |
| ens37 | Internet temporal |
| ens40 | Trunk 2 → pfSense Backup |

### Core 2
| Interfaz | Función |
|---|---|
| ens34 | Trunk 2 → pfSense Backup |
| ens35 | Internet temporal |
| ens36 | Interlink → Core 1 |
| ens39 | Internet backup |
| ens40 | Trunk 1 → pfSense Master |

---

## Ejecución

### Deploy completo por sitio
```bash
# Lima (cores HA + servicios)
ansible-playbook playbooks/site.yml --tags lima

# Arequipa (core + DHCP + DNS + VPN)
ansible-playbook playbooks/site.yml --tags arequipa

# Trujillo (core + DHCP + DNS + VPN)
ansible-playbook playbooks/site.yml --tags trujillo

# Todo junto
ansible-playbook playbooks/site.yml --tags all
```

### Deploy individual
```bash
# Solo los cores de Lima en HA
ansible-playbook playbooks/lima/00_core_ha.yml

# Solo Arequipa
ansible-playbook playbooks/arequipa/00_sede_base.yml

# Solo Trujillo
ansible-playbook playbooks/trujillo/00_sede_base.yml
```

### Diagnósticos
```bash
# Verificar red en todos los sitios
ansible-playbook playbooks/common/diagnostics.yml --tags network -e target_sites=all

# Verificar DHCP
ansible-playbook playbooks/common/diagnostics.yml --tags dhcp -e target_sites=all

# Verificar VPN
ansible-playbook playbooks/common/diagnostics.yml --tags vpn -e target_sites=all
```

---

## ESXi — Conexión

| Parámetro | Valor |
|---|---|
| URL | `https://168.121.48.254:10112/ui/#/host/vms` |
| Usuario | `root` |
| Contraseña | `qwe123$` |

---

## Verificación Post-Instalación

### Core Lima (HA)
```bash
# Estado Keepalived
sudo systemctl status keepalived
ip addr show | grep "inet.*br"

# OSPF
sudo vtysh -c "show ip ospf neighbor"
sudo vtysh -c "show ip ospf route"

# VIP activa
ip addr show br20 | grep "inet "
```

### Sedes Remotas
```bash
# DHCP activo
sudo systemctl status isc-dhcp-server
journalctl -u isc-dhcp-server --no-pager -n 10

# DNS forwarder
dig @127.0.0.1 google.com +short
dig @127.0.0.1 vm-dc01.AJ.local

# VPN activa
wg show
ip route show | grep wg
```

---

## Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `Fatal: interface X no existe` | NICs con nombres diferentes | Editar `nic_trunk1`, `bonded_nics` en el playbook |
| `netplan generate` falla | Sintaxis YAML incorrecta | Verificar templates/netplan.yaml.j2 |
| OSPF no forma vecindad | Sin conectividad interlink | Ping 10.0.0.1 ↔ 10.0.0.2 |
| VIP duplicadas (split-brain) | Ambos cores MASTER | Verificar conectividad interlink y priority |
| DHCP no entrega IPs | Interfaces bridged no levantan | `ip -br a` verificar br20, br60 |
| DNS no resuelve externo | Forwarders mal configurados | Revisar dns_forwarders en group_vars |
| WireGuard handshake falla | Claves o endpoints incorrectos | Verificar wg0.conf en sede remota |

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-06-09 | Reestructuración multi-sitio: Lima (HA), Arequipa, Trujillo |
| 2026-06-09 | Rol `sede_remota` creado: networking + DHCP + DNS + VPN |
| 2026-06-09 | group_vars/ separados por sede |
| 2026-06-09 | playbook site.yml maestro contags por sede |
| 2026-06-09 | Inventario actualizado con grupos lima/arequipa/trujillo |

---

## Licencia

MIT — PRs bienvenidos.