# =============================================================================
# MAPA DE RED COMPLETO — Universidad Peru S.A.C.
# =============================================================================
# Última actualización: 2026-06-10
# =============================================================================

# =============================================================================
# LIMA — SEDE PRINCIPAL (HA)
# =============================================================================

## -------------------------------------------------------------------------
# CORE 1 (MASTER Keepalived - Prioridad 200)
# -------------------------------------------------------------------------
# Interfaz     | Connected to          | IP              | Notes
# -------------|----------------------|-----------------|-----------------------
# ens34        | Trunk-LANT1-pfSense1  | trunk (tagged)  | Todas las VLANs
# ens35        | Acceso Directo        | N/A             | Reservada
# ens36        | Interlink Core2       | 10.0.0.1/30     | OSPF + VRRP heartbeats
# ens37        | Internet temp        | N/A             | Temporal
# ens40        | Trunk2-LANT2-pfSense2| trunk (tagged)  | HA con pfSense Backup

## Puentes (Bridges) en Core 1:
# Bridge | VLAN | IP              | VIP (Keepalived) | VRID
# -------|---|-----------------|-------------------|-----
# br10   | 10   | 192.168.11.4/27 | 192.168.11.1/27  | 10
# br20   | 20   | 192.168.12.4/25 | 192.168.12.1/25  | 20
# br21   | 21   | 192.168.21.4/27 | 192.168.21.1/27  | 21
# br30   | 30   | 192.168.13.4/25 | 192.168.13.1/25  | 30
# br40   | 40   | 192.168.14.4/26 | 192.168.14.1/26  | 40
# br50   | 50   | 192.168.15.4/26 | 192.168.15.1/26  | 50
# br60   | 60   | 192.168.16.4/27 | 192.168.16.1/27  | 60
# br70   | 70   | 192.168.17.4/27 | 192.168.17.1/27  | 70
# br999  | 999  | 192.168.99.4/30 | 192.168.99.1/30  | 254 (HA Sync)

## Keepalived:
# - Estado: MASTER
# - Prioridad: 200 (baja a 105 en split-brain, sube a 205 recovery)
# - Src IP: 10.0.0.1
# - Peer IP: 10.0.0.2
# - Unicast VRRP habilitado

## OSPF:
# - Router ID: 10.0.0.1
# - Area: 0.0.0.0

# -------------------------------------------------------------------------
# CORE 2 (BACKUP Keepalived - Prioridad 100)
# -------------------------------------------------------------------------
# Interfaz     | Connected to          | IP              | Notes
# -------------|----------------------|-----------------|-----------------------
# ens34        | Trunk2-LANT2-pfSense2 | trunk (tagged)  | Todas las VLANs
# ens35        | Internet temp         | N/A             | Temporal
# ens36        | Interlink Core1       | 10.0.0.2/30     | OSPF + VRRP heartbeats
# ens39        | Internet backup      | N/A             | Temporal
# ens40        | Trunk1-LANT1-pfSense1 | trunk (tagged)  | HA con pfSense Master

## Puentes (Bridges) en Core 2:
# Bridge | VLAN | IP              | VIP (Keepalived) | VRID
# -------|---|-----------------|-------------------|-----
# br10   | 10   | 192.168.11.5/27 | 192.168.11.1/27  | 10
# br20   | 20   | 192.168.12.5/25 | 192.168.12.1/25  | 20
# br21   | 21   | 192.168.21.5/27 | 192.168.21.1/27  | 21
# br30   | 30   | 192.168.13.5/25 | 192.168.13.1/25  | 30
# br40   | 40   | 192.168.14.5/26 | 192.168.14.1/26  | 40
# br50   | 50   | 192.168.15.5/26 | 192.168.15.1/26  | 50
# br60   | 60   | 192.168.16.5/27 | 192.168.16.1/27  | 60
# br70   | 70   | 192.168.17.5/27 | 192.168.17.1/27  | 70
# br999  | 999  | 192.168.99.5/30 | 192.168.99.1/30  | 254 (HA Sync)

## Keepalived:
# - Estado: BACKUP
# - Prioridad: 100
# - Src IP: 10.0.0.2
# - Peer IP: 10.0.0.1
# - Unicast VRRP habilitado
# - nopreempt habilitado

## OSPF:
# - Router ID: 10.0.0.2
# - Area: 0.0.0.0

# =============================================================================
# VLANs — LIMA (Subnets y uso)
# =============================================================================

# VLAN | Nombre          | Subnet             | Gateway (VIP) | Usado por
# -----|-----------------|--------------------|----------------|-------------------
# 10   | DMZ             | 192.168.11.0/27    | 192.168.11.1   | vm-web01
# 20   | Usuarios        | 192.168.12.0/25    | 192.168.12.1   | PCs usuarios (DHCP)
# 21   | Administracion  | 192.168.21.0/27    | 192.168.21.1   | Admin PCs
# 30   | Virtualizacion  | 192.168.13.0/25    | 192.168.13.1   | VMs servicios
# 40   | Storage         | 192.168.14.0/26    | 192.168.14.1   | NFS/SAN
# 50   | VoIP            | 192.168.15.0/26    | 192.168.15.1   | FreePBX/Telefonia
# 60   | Gestion         | 192.168.16.0/27    | 192.168.16.1   | vm-dc01 (AD/DNS/DHCP)
# 70   | Monitoreo       | 192.168.17.0/27    | 192.168.17.1   | vm-monitor01
# 999  | HA Sync         | 192.168.99.0/30    | 192.168.99.1   | pfSense HA Sync

# =============================================================================
# PFSENSE — LIMA (HA)
# =============================================================================

# pfSense Master (LANT-1):
# - WAN: DHCP del ISP
# - LAN (Trunk): 192.168.16.2 (VLAN 60)
# - CARP VIPs: 192.168.X.1 en cada VLAN
# - Sync: 192.168.99.2

# pfSense Backup (LANT-2):
# - WAN: DHCP del ISP
# - LAN (Trunk): 192.168.16.3 (VLAN 60)
# - CARP VIPs: Compartidas con Master
# - Sync: 192.168.99.3

# =============================================================================
# VMs — LIMA
# =============================================================================

# VM           | VLANs | IP estatica       | Servicios
# -------------|-------|------------------|-------------------------------
# vm-dc01      | 60    | 192.168.16.10    | Samba 4 AD + DNS + DHCP
# vm-services01| 30    | 192.168.30.11    | Samba file shares + iRedMail
# vm-web01     | 10,30 | 192.168.11.11    | Nginx + HAProxy + PostgreSQL
# vm-voip01    | 30,50 | 192.168.50.11    | FreePBX + Asterisk
# vm-monitor01 | 70    | 192.168.17.11    | Zabbix + Grafana
# vm-storage01 | 30,40 | 192.168.40.11    | NFS + PBS + rclone
# vm-docker01  | 30    | 192.168.30.12    | Docker + Docker Compose

# =============================================================================
# POOLs DHCP — VLAN 20 (Usuarios)
# =============================================================================

# Pool              | Rango IP             | Para
# ------------------|----------------------|-------------------------------
# admins_devs       | 192.168.12.5-14      | Administradores, Devs
# pool_devs         | 192.168.12.15-30     | Desarrollo
# pool_rrhh         | 192.168.12.31-50     | RRHH, Finanzas
# pool_operaciones  | 192.168.12.51-80     | Operaciones, Logistica
# pool_general      | 192.168.12.81-200    | Usuarios generales

# =============================================================================
# INTERLINK Y CONECTIVIDAD
# =============================================================================

# Core1 ↔ Core2 (cable cruzado):
# - Core1 ens36: 10.0.0.1/30
# - Core2 ens36: 10.0.0.2/30

# =============================================================================
# AREQUIPA — SEDE REMOTA
# =============================================================================

# VLAN | Nombre  | Subnet             | Gateway | Usado por
# -----|---------|-------------------|---------|------------------
# 20   | Usuarios| 192.168.82.0/25   | 192.168.82.1 | PCs usuarios
# 60   | Gestion | 192.168.87.0/27   | 192.168.87.1 | Servers locales

# Core-AQP:
# - wan: DHCP ISP
# - lan (br20): 192.168.82.2/25
# - br60: 192.168.87.2/27
# - VPN: WireGuard client → Lima
# - DNS: Bind9 forwarder → 192.168.16.10

# Pools DHCP Arequipa:
# - 192.168.82.50-200 (VLAN 20)
# - 192.168.87.10-20 (VLAN 60)

# =============================================================================
# TRUJILLO — SEDE REMOTA
# =============================================================================

# VLAN | Nombre  | Subnet             | Gateway | Usado por
# -----|---------|-------------------|---------|------------------
# 20   | Usuarios| 192.168.92.0/25   | 192.168.92.1 | PCs usuarios
# 60   | Gestion | 192.168.97.0/27   | 192.168.97.1 | Servers locales

# Core-TRU:
# - wan: DHCP ISP
# - lan (br20): 192.168.92.2/25
# - br60: 192.168.97.2/27
# - VPN: WireGuard client → Lima
# - DNS: Bind9 forwarder → 192.168.16.10

# Pools DHCP Trujillo:
# - 192.168.92.50-200 (VLAN 20)
# - 192.168.97.10-20 (VLAN 60)

# =============================================================================
# RESUMEN DE IPs EN USO — LIMA
# =============================================================================

# En VLAN 60 (Gestion) — Rango: 192.168.16.0/27
# .1   = VIP Keepalived (HA)
# .2   = pfSense Master
# .3   = pfSense Backup
# .4   = Core 1 (br60)
# .5   = Core 2 (br60)
# .10  = vm-dc01 (AD/DNS/DHCP) ← NUEVO
# .11  = vm-services01
# .254 = pfSync CARP VIP

# =============================================================================
# RESUMEN DE IPs RESERVADAS / LIBRES
# =============================================================================

# 192.168.11.0/27 (VLAN 10 - DMZ):
# .2-.10 = libres
# .11 = vm-web01

# 192.168.12.0/25 (VLAN 20 - Usuarios):
# .2-.4 = libres (gateway en .1)
# .5-14 = pool admins_devs
# .15-30 = pool devs
# .31-50 = pool rrhh
# .51-80 = pool operaciones
# .81-200 = pool general
# .201-254 = libres

# 192.168.16.0/27 (VLAN 60 - Gestion):
# .6-.9 = libres
# .10 = vm-dc01 (DHCP/DNS/AD)
# .11 = vm-services01
# .12-.30 = libres

# =============================================================================
# FORMATO DE NOMBRES DE HOST
# =============================================================================

# Dominio: AJ.local
# Hostnames:
# - dc01.AJ.local         (vm-dc01)
# - core1.AJ.local         (Core 1)
# - core2.AJ.local         (Core 2)
# - services01.AJ.local    (vm-services01)
# - web01.AJ.local         (vm-web01)
# - voip01.AJ.local        (vm-voip01)
# - monitor01.AJ.local     (vm-monitor01)
# - storage01.AJ.local      (vm-storage01)
# - docker01.AJ.local      (vm-docker01)

# =============================================================================
# NOTAS
# =============================================================================

# 1. vm-dc01 tiene bonding ens34+ens35 para HA
# 2. DHCP relay en pfSense reenvía peticiones a 192.168.16.10
# 3. Core 1 y Core 2 usan VRRP unicast (multicast bloqueado)
# 4. Interlink 10.0.0.0/30 es para OSPF y VRRP heartbeats
# 5. pfSense HA usa CARP, Cores usan Keepalived (no conflictan)