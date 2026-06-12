# =============================================================================
# MAPA DE RED - TUEMPRESA PERÚ S.A.C.
# 3 SEDES: LIMA, AREQUIPA, TRUJILLO
# =============================================================================
# Última actualización: 2026-06-11
# =============================================================================

# =============================================================================
# LIMA - SEDE PRINCIPAL (HA)
# =============================================================================

## Infraestructura:
# - 2x pfSense en HA (CARP)
# - 2x Core Linux en HA (Keepalived + OSPF)
# - 1x vm-dc01 (Samba AD + DNS + DHCP)
# - Servicios varios

## pfSense Lima:
# WAN: DHCP del ISP
# LAN/Trunk: 192.168.16.2 (Master), 192.168.16.3 (Backup)
# CARP VIP: 192.168.16.1

## Core 1 (MASTER):
# - ens34: Trunk → pfSense Master (brX-vlans)
# - ens36: Interlink 10.0.0.1
# - ens37: LAN-1 → pfSense Master (192.168.10.1) - Gateway internet
# - ens40: Trunk → pfSense Backup (brX-vlans)
# - ens41: LAN-2 → pfSense Backup (192.168.10.1) - Gateway internet HA
# Bonding ens37+ens41: bond0 con IP 192.168.10.20/24 (HA failover)
# VIPs Keepalived en cada VLAN

## Core 2 (BACKUP):
# - ens34: Trunk → pfSense Backup (brX-vlans)
# - ens36: Interlink 10.0.0.2
# - ens39: LAN-1 → pfSense Master (192.168.10.1) - Gateway internet
# - ens40: Trunk → pfSense Master (brX-vlans)
# - ens41: LAN-2 → pfSense Backup (192.168.10.1) - Gateway internet HA
# Bonding ens39+ens41: bond0 con IP 192.168.10.30/24 (HA failover)
# VIPs Keepalived en cada VLAN

## VLANs Lima y Subnets:
# VLAN 10 - DMZ:       192.168.11.0/27  | VIP: 192.168.11.1 | Core1: .4, Core2: .5
# VLAN 20 - Usuarios: 192.168.12.0/25  | VIP: 192.168.12.1 | Core1: .4, Core2: .5
# VLAN 21 - Admin:     192.168.21.0/27  | VIP: 192.168.21.1 | Core1: .4, Core2: .5
# VLAN 30 - Virtualiz: 192.168.13.0/25  | VIP: 192.168.13.1 | Core1: .4, Core2: .5
# VLAN 40 - Storage:   192.168.14.0/26  | VIP: 192.168.14.1 | Core1: .4, Core2: .5
# VLAN 50 - VoIP:       192.168.15.0/26  | VIP: 192.168.15.1 | Core1: .4, Core2: .5
# VLAN 60 - Gestión:    192.168.16.0/27  | VIP: 192.168.16.1 | Core1: .4, Core2: .5, vm-dc01: .10
# VLAN 70 - Monitor:    192.168.17.0/27  | VIP: 192.168.17.1 | Core1: .4, Core2: .5
# VLAN 999 - HA Sync:   192.168.99.0/30  | VIP: 192.168.99.1 | Core1: .4, Core2: .5

## vm-dc01 (Samba AD + DNS + DHCP):
# - IP: 192.168.16.10/27
# - Bonding: ens34 + ens35 → bond0
# - Dominio: AJ.local
# - DHCP Pool usuarios: 192.168.12.81-200

## IPs en uso en VLAN 60:
# .1  = VIP Keepalived (Gateway)
# .2  = pfSense Master
# .3  = pfSense Backup
# .4  = Core 1 (br60)
# .5  = Core 2 (br60)
# .10 = vm-dc01 (AD/DNS/DHCP)

## IPs LAN PF para acceso a internet (routing):
# .20 = Core 1 (bond0: ens37+ens41)
# .30 = Core 2 (bond0: ens39+ens41)

# TABLA RESUMEN DE INTERFACES (Lima):
# +------------+------------+--------------------------------+------------------+
# | Core       | Interfaz   | Descripción                    | IP/Mask          |
# +------------+------------+--------------------------------+------------------+
# | Core 1     | ens34      | Trunk 1 → pfSense Master       |802.1q brX-vlans  |
# | Core 1     | ens36      | Interlink Core 1→2             | 10.0.0.1/30      |
# | Core 1     | ens37      | LAN-1 → pfSense Master         | Bond Slave       |
# | Core 1     | ens40      | Trunk 2 → pfSense Backup       |802.1q brX-vlans  |
# | Core 1     | ens41      | LAN-2 → pfSense Backup         | Bond Slave       |
# | Core 1     | bond0      | Bond (ens37+ens41)             | 192.168.10.20/24 |
# +------------+------------+--------------------------------+------------------+
# | Core 2     | ens34      | Trunk 2 → pfSense Backup       |802.1q brX-vlans  |
# | Core 2     | ens36      | Interlink Core 2→1             | 10.0.0.2/30      |
# | Core 2     | ens39      | LAN-1 → pfSense Master         | Bond Slave       |
# | Core 2     | ens40      | Trunk 1 → pfSense Master       |802.1q brX-vlans  |
# | Core 2     | ens41      | LAN-2 → pfSense Backup         | Bond Slave       |
# | Core 2     | bond0      | Bond (ens39+ens41)             | 192.168.10.30/24 |
# +------------+------------+--------------------------------+------------------+

# =============================================================================
# AREQUIPA - SEDE REMOTA (Simple)
# =============================================================================

## Infraestructura:
# - 1x pfSense (SIN HA, single)
# - 1x Core Linux (sin HA, single)
# - DHCP local, DNS forward a Lima

## pfSense Arequipa:
# WAN: DHCP del ISP (o IP fija pública)
# LAN: 192.168.82.1 ( gateway para usuarios )

## Core Arequipa:
# - WAN: DHCP del ISP
# - LAN/Trunk: 192.168.82.2/25 (br20), 192.168.87.2/27 (br60)
# - VPN client WireGuard → Lima

## VLANs Arequipa y Subnets:
# VLAN 20 - Usuarios: 192.168.82.0/25 | Gateway: 192.168.82.1 | Core: .2
# VLAN 60 - Gestión:  192.168.87.0/27 | Gateway: 192.168.87.1 | Core: .2

## DHCP en Arequipa (CORE):
# Pool usuarios: 192.168.82.50-200 (150 IPs)

## Core Arequipa IPs:
# - br20 (VLAN 20): 192.168.82.2/25
# - br60 (VLAN 60): 192.168.87.2/27

## VPN Arequipa → Lima:
# WireGuard client en Core Arequipa
# Endpoint: IP pública de Lima
# AllowedIPs: 192.168.0.0/16


# =============================================================================
# TRUJILLO - SEDE REMOTA (Simple)
# =============================================================================

## Infraestructura:
# - 1x pfSense (SIN HA, single)
# - 1x Core Linux (sin HA, single)
# - DHCP local, DNS forward a Lima

## pfSense Trujillo:
# WAN: DHCP del ISP (o IP fija pública)
# LAN: 192.168.92.1 ( gateway para usuarios )

## Core Trujillo:
# - WAN: DHCP del ISP
# - LAN/Trunk: 192.168.92.2/25 (br20), 192.168.97.2/27 (br60)
# - VPN client WireGuard → Lima

## VLANs Trujillo y Subnets:
# VLAN 20 - Usuarios: 192.168.92.0/25 | Gateway: 192.168.92.1 | Core: .2
# VLAN 60 - Gestión:  192.168.97.0/27 | Gateway: 192.168.97.1 | Core: .2

## DHCP en Trujillo (CORE):
# Pool usuarios: 192.168.92.50-200 (150 IPs)

## Core Trujillo IPs:
# - br20 (VLAN 20): 192.168.92.2/25
# - br60 (VLAN 60): 192.168.97.2/27

## VPN Trujillo → Lima:
# WireGuard client en Core Trujillo
# Endpoint: IP pública de Lima
# AllowedIPs: 192.168.0.0/16


# =============================================================================
# CONECTIVIDAD ENTRE SEDES (VPN WireGuard)
# =============================================================================

## Lima (Server):
# WireGuard Listen Port: 51820
# Interfaz: wg0
# IP: 10.200.255.1/30

## Arequipa (Client):
# IP: 10.200.0.2/30
# Peer: Lima (10.200.255.1)
# AllowedIPs: 192.168.0.0/16

## Trujillo (Client):
# IP: 10.200.1.2/30
# Peer: Lima (10.200.255.1)
# AllowedIPs: 192.168.0.0/16


# =============================================================================
# RESUMEN DE IPs POR SEDE
# =============================================================================

# LIMA:
# 192.168.11.x - DMZ
# 192.168.12.x - Usuarios (DHCP relay → vm-dc01)
# 192.168.13.x - Virtualización
# 192.168.14.x - Storage
# 192.168.15.x - VoIP
# 192.168.16.x - Gestión (AD/DNS/DHCP central)
# 192.168.17.x - Monitoreo

# AREQUIPA:
# 192.168.82.x - Usuarios (DHCP local en Core)
# 192.168.87.x - Gestión

# TRUJILLO:
# 192.168.92.x - Usuarios (DHCP local en Core)
# 192.168.97.x - Gestión


# =============================================================================
# NOTAS
# =============================================================================

# 1. Arequipa y Trujillo usan DHCP local en el Core (NO relay a Lima)
# 2. DNS siempre forward a Lima (192.168.16.10) para resolver AJ.local
# 3. VPN WireGuard conecta sedes remotas a Lima
# 4. Los servicios web/críticos vienen de Lima
# 5. Cada sede tiene su propia subred para usuarios