# ============================================================================
# Topología de VMs del laboratorio
# ============================================================================

## ESXi Host
- **IP:** 168.121.48.254:10112
- **Credenciales:** root / qwe123$

## Inventario de VMs

| VM Name | OS | RAM | CPU | Servicios | VLANs |
|---|---|---|---|---|---|
| **vm-dc01** | Windows Server 2022 | 4GB | 4 | AD, DNS, DHCP, GPO, CA | 30, 60 |
| **vm-services01** | Ubuntu 24.04 | 1GB | 2 | Samba, iRedMail | 30 |
| **vm-web01** | Ubuntu 24.04 | 512MB | 2 | Nginx, HAProxy, PostgreSQL | 10, 30 |
| **vm-voip01** | Ubuntu 24.04 | 512MB | 2 | FreePBX | 30, 50 |
| **vm-monitor01** | Ubuntu 24.04 | 1GB | 2 | Zabbix, Grafana | 70 |
| **vm-storage01** | Ubuntu 24.04 | 512MB | 2 | NFS, PBS, rclone | 30, 40 |
| **vm-docker01** | Ubuntu 24.04 | 512MB | 2 | Docker, Docker Compose | 30 |

## Mapeo de VLANs

| VLAN | Nombre | VMs asociadas |
|------|--------|--------------|
| 10 | DMZ | vm-web01 |
| 30 | Virtualización | vm-dc01, vm-services01, vm-web01, vm-voip01, vm-storage01, vm-docker01 |
| 40 | Storage | vm-storage01 |
| 50 | VoIP | vm-voip01 |
| 60 | Gestión | vm-dc01 |
| 70 | Monitoreo | vm-monitor01 |

## Notas

- **vm-dc01** es Windows Server 2022. No se automatiza con estos playbooks.
- Todas las demás VMs son **Ubuntu Server 24.04**.
- Cada VM Ubuntu debería ejecutar su playbook correspondiente de aprovisionamiento.
