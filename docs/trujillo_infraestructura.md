# ============================================================================
# TRUJILLO — DOCUMENTACIÓN DE INFRAESTRUCTURA
# ============================================================================
# Sede: Trujillo
# Dominio: AXIOM.LOCAL (réplica local)
# ISP: isp-tru01 (192.169.92.1/24)
# ============================================================================

## 1. TOPOLOGÍA DE RED

```
                     INTERNET
                        |
                  [ISP-TRU]
                  NAT/LAN
                192.169.92.1/24
                        |
                [pfSense-TRU]
                CARP VIPs 192.169.92.x
                        |
            +-----------+-----------+
            |                       |
       [core-tru1]           [core-tru2]
       192.169.92.2          192.169.92.3
       OSPF + STP            OSPF + STP
            |                       |
       +----+----+---+---+----+---+----+
       |           |           |        |
    VLAN 20    VLAN 40    VLAN 60    VLAN 99
    Usuarios   Storage    Gestión    HA Sync
```

---

## 2. TABLA IP — TRUJILLO

### VLANs y Subnets:

| VLAN ID | Nombre | Subnet | Gateway (pfSense VIP) | Rango IPs |
|---------|--------|--------|----------------------|-----------|
| **20** | Usuarios | `192.169.92.0/24` | `192.169.92.1` | `.100` - `.200` |
| **40** | Storage | `192.169.94.0/26` | `192.169.94.1` | `.10` - `.62` |
| **60** | Gestión | `192.169.92.60/27` | `192.169.92.61` | `.62` - `.90` |
| **99** | HA Sync | `10.2.0.0/30` | — | `.1` - `.2` |

### Máquinas Virtuales:

| VM | IP | VLAN | vCPU | RAM | Servicios |
|----|-----|------|------|-----|-----------|
| **isp-tru01** | WAN: DHCP / LAN: `192.169.92.1/24` | — | 2 | 2GB | NAT + Routing |
| **pfSense-TRU** | `192.169.92.1` (VIP CARP) | Trunk | 2 | 2GB | Firewall, NAT, VPN |
| **core-tru1** | `192.169.92.2/24` | Trunk | 2 | 4GB | FRR OSPF, STP root |
| **core-tru2** | `192.169.92.3/24` | Trunk | 2 | 4GB | FRR OSPF, STP backup |
| **tru-dc01** | `192.169.92.10/27` | 60 | 2 | 2GB | AD DC, DNS, DHCP |
| **tru-dns01** | `192.169.92.11/27` | 60 | 1 | 2GB | DNS secundario |
| **tru-voip01** | `192.169.92.12/27` | 60 | 1 | 2GB | Asterisk local |
| **tru-storage01** | `192.169.94.11/26` | 40 | 1 | 2GB | Samba + NFS |

---

## 3. ENRUTAMIENTO OSPF

### Configuración de cores:

**core-tru1:**
- Router ID: `10.2.0.1`
- Interlink HA: `10.2.0.1/30` (hacia core-tru2)
- Redes anunciadas:
  - `192.169.92.0/24` (VLANs 20 + 60)
  - `192.169.94.0/26` (VLAN 40 - Storage)
  - `10.2.0.0/30` (Interlink HA)
- STP Priority: `4096` (root bridge)

**core-tru2:**
- Router ID: `10.2.0.2`
- Interlink HA: `10.2.0.2/30` (hacia core-tru1)
- Redes anunciadas: Mismas que core-tru1
- STP Priority: `8192` (backup root)

### Rutas estáticas en pfSense:
- Default route → ISP (`0.0.0.0/0` → `192.169.92.254` o DHCP)
- Ruta hacia Lima → VPN Tailscale (cuando esté activa)

---

## 4. SERVICIOS LOCALES

### 4.1 Active Directory (tru-dc01)
- **Dominio**: `AXIOM.LOCAL` (réplica local independiente)
- **Realm**: `AXIOM.LOCAL`
- **Workgroup**: `AXIOM`
- **IP**: `192.169.92.10/27`
- **Gateway**: `192.169.92.61` (VLAN 60)
- **DNS**: `192.169.92.10` (primario), `192.169.92.11` (secundario)
- **DHCP Ranges**:
  - VLAN 20: `192.169.92.100` - `192.169.92.200`
  - VLAN 60: `192.169.92.70` - `192.169.92.90`

### 4.2 DNS (tru-dns01)
- **Rol**: DNS secundario (slave de tru-dc01)
- **IP**: `192.169.92.11/27`
- **Transferencia AXFR**: Desde `192.169.92.10`

### 4.3 VoIP (tru-voip01)
- **Servicio**: Asterisk 20.6
- **IP**: `192.169.92.12/27`
- **Extensiones**: 200, 201, 202 (locales)
- **Trunk SIP**: Hacia Lima (por Tailscale)

### 4.4 Storage (tru-storage01)
- **Rol**: File Server (Samba + NFS)
- **IP**: `192.169.94.11/26`
- **Gateway**: `192.169.94.1` (VLAN 40)
- **Shares SMB**:
  - `Jefatura` → `@AXIOM\administradores` (192.169.92.10-80)
  - `Secretaria` → `@AXIOM\secretaria` (192.169.92.81-100)
  - `Usuarios` → `@AXIOM\Domain Users` (192.169.92.101-200)
  - `Publico` → Guest
  - `Proyectos` → `@AXIOM\Domain Users`
- **NFS Exports**:
  - `/shared/publico` → 192.169.92.0/24, 192.169.94.0/26
  - `/shared/proyectos` → 192.169.92.0/24, 192.169.94.0/26

---

## 5. CONECTIVIDAD CON OTRAS SEDES

### Tailscale (VPN site-to-site):
- **Nodo Trujillo**: tru-dc01 (o VM dedicada)
- **Rutas anunciadas**: `192.169.92.0/24`, `192.169.94.0/26`
- **Rutas remotas**:
  - Lima: `192.168.0.0/16`
  - Arequipa: `192.167.0.0/16`

### Servicios consumidos desde Trujillo:
| Servicio | Sede | VM | IP | Accesible por |
|----------|------|-----|-----|---------------|
| WordPress | Lima | vm-web01/02 | 192.168.10.11/12 | Tailscale |
| Email | Lima | vm-services01 | 192.168.30.11 | Tailscale |
| Dolibarr | Lima | vm-services01 | 192.168.30.11 | Tailscale |
| Zabbix Server | Lima | vm-monitor01 | 192.168.70.11 | Tailscale |
| AD Master | Lima | vm-dc01 | 192.168.60.10 | Tailscale (respaldo) |

---

## 6. PLAYBOOKS DISPONIBLES PARA TRUJILLO

| Playbook | Propósito | Estado |
|----------|-----------|--------|
| `tru-core1_network.yml` | Red + OSPF + STP (core-tru1) | ⏳ Pendiente |
| `tru-core2_network.yml` | Red + OSPF + STP (core-tru2) | ⏳ Pendiente |
| `tru-dc01.yml` | AD + DNS + DHCP | ⏳ Pendiente |
| `tru-dns01.yml` | DNS secundario | ⏳ Pendiente |
| `tru-voip01.yml` | Asterisk local | ⏳ Pendiente |
| `tru-storage01.yml` | Samba + NFS | ⏳ Pendiente |
| `tru-pfsense_openvpn.yml` | OpenVPN site-to-site | ⏳ Pendiente |
| `tru-tailscale.yml` | Tailscale client | ⏳ Pendiente |

---

## 7. CREDENCIALES — TRUJILLO

| Servicio | Usuario | Password | Nota |
|----------|---------|----------|------|
| **AD Admin** | Administrator | admin123! | Local de Trujillo |
| **AD Users** | jefazo, secretaria, contador | rol.123 | Mismos que Lima/Aqp |
| **SSH VMs** | ubuntu | 123 | Todas las VMs |
| **Samba** | jefazo / secretaria / contador | rol.123 | Shares locales |
| **pfSense** | admin | pfsense | Firewall local |
| **Asterisk** | 200, 201, 202 | rol.123 | Extensiones locales |

---

## 8. PRÓXIMOS PASOS

1.  ✅ **Crear VMs en ESXi** (core-tru1, core-tru2, tru-dc01, etc.)
2.  ⏳ **Configurar red + OSPF** (core-tru1, core-tru2)
3.  ⏳ **Configurar pfSense** (VLANs + CARP + OpenVPN/Tailscale)
4.  ⏳ **Levantar AD local** (tru-dc01)
5.  ⏳ **Configurar servicios** (DNS, DHCP, VoIP, Storage)
6.  ⏳ **Conectar con Tailscale** a Lima y Arequipa

---

**Fecha de creación**: 2026-07-02
**Última actualización**: 2026-07-02
**Autor**: Diego (opencode assistant)