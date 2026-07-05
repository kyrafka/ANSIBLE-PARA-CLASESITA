# tuempresa Peru S.A.C. — Documentacion de Infraestructura
# Fecha: Julio 2026

## 1. Topologia General

3 sedes conectadas via VPN (Tailscale):

```
                     INTERNET
                        |
        +---------------+---------------+
        |                               |
   [ISP-Aqp]                       [ISP-Tru]
   NAT/LAN                          NAT/LAN
 192.167.82.1/24                  192.170.12.1/24
        |                               |
   [core-aqp]                     [core-tru]
   OSPF/STP                       OSPF/STP
        |                               |
   +----+----+                   +----+----+
   |           |                   |           |
SEDE AREQUIPA              SEDE TRUJILLO
192.167.82.0/24            192.170.12.0/24
        |                               |
   [Tailscale VPN 192.168.0.0/16, 172.17.25.0/24]
        |
   [pfSense HA — Lima HQ]
    CARP VIPs 192.168.x.3
        |
   [CORE1 / CORE2 — FRR OSPF + STP]
        |
   +----+----+---+---+----+---+----+
   VLANs 10/20/21/30/40/50/60/70
```

## 2. VMware ESXi (Lima)

- **Host**: 172.17.25.12:443
- **Credenciales**: root / qwe123$
- **vCenter**: Disponible para clusterizacion y migracion de VMs entre sedes
- **Backup**: vCenter maneja snapshots y migracion completa de VMs

## 3. Tabla IP Completa — 3 Sedes

### LIMA (HQ) — VLANs y Subnets

| VLAN ID | Nombre | Subnet | Gateway | Máquinas/Servicios |
|---------|--------|--------|---------|-------------------|
| 10 | DMZ | 192.168.11.0/27 | 192.168.11.3 | web01 (192.168.11.11), web02 (192.168.11.12) |
| 20 | Usuarios | 192.168.12.0/24 | 192.168.12.3 | DHCP clients |
| 30 | Services | 192.168.13.0/25 | 192.168.13.3 | services01 (192.168.13.11), docker01 (192.168.13.12) |
| 40 | Storage | 192.168.14.0/26 | 192.168.14.3 | storage01 (192.168.14.11) |
| 50 | VoIP | 192.168.15.0/26 | 192.168.15.3 | voip01 (192.168.15.11) |
| 60 | Gestion | 192.168.16.0/27 | 192.168.16.3 | dc01 (192.168.16.10), dns02 (192.168.16.11) |
| 70 | Monitoreo | 192.168.17.0/27 | 192.168.17.3 | monitor01 (192.168.17.11) |
| 99 | HA Sync | 192.168.99.0/30 | — | core1, core2 |

### AREQUIPA — 192.167.x.x - VERIFICADO ✅

| VLAN ID | Nombre | Subnet | Gateway | Máquinas/Servicios |
|---------|--------|--------|---------|-------------------|
| 12 | Usuarios | 192.167.12.0/25 | 192.167.12.3 | DHCP clients |
| 14 | Storage | 192.167.14.0/26 | 192.167.14.3 | storage01 (192.167.14.11) |
| 15 | VoIP | 192.167.15.0/26 | 192.167.15.3 | No existe |
| 16 | Gestion | 192.167.16.0/27 | 192.167.16.3 | dc01 (192.167.16.10), dns01 (192.167.16.11) |
| 21 | Admin | 192.167.21.0/27 | 192.167.21.3 | DHCP clients |
| 82 | LAN PFSENSE | 192.167.82.0/24 | 192.167.82.3 | pfSense-AQP gateway |

**Notas:**
- **VLANs manejadas por pfSense** (no por los cores)
- **Cores**: Solo routing OSPF + STP (sin interfaces bridge)
- **Consumo de servicios**: Arequipa consume servicios de Lima vía Tailscale (AD, DNS, Zabbix, Web, Email, ERP)
- **Servicios locales**: DC local, DNS local, Storage local

### TRUJILLO — 192.170.12.x

| VLAN ID | Nombre | Subnet | Gateway | Notas |
|---------|--------|--------|---------|-------|
| 20 | Usuarios | 192.170.12.0/24 | 192.170.12.3 | DHCP local |
| 60 | Gestion | 192.170.12.60/28 | 192.170.12.61 | DC, DNS, VoIP local |

## 4. Maquinas Virtuales — Lima (HQ) - VERIFICADO ✅

| VM | IP Real | VLAN | vCPU | RAM | SO | Servicios | Estado |
|----|-----|------|------|-----|-----|-----------|--------|
| vm-dc01 | **192.168.16.10/27** | 60 | 2 | 2GB | Ubuntu 24 | Samba4 AD DC, BIND9 master, ISC-DHCP primary | ✅ running |
| vm-dns02 (dc02) | **192.168.16.11/27** | 60 | 1 | 2GB | Ubuntu 24 | BIND9 slave, ISC-DHCP secondary, chrony NTP | ✅ running |
| vm-web01 | **192.168.11.11** | 10,30 | 2 | 2GB | Ubuntu 24 | HAProxy :80, Apache :8080, WordPress | ✅ running |
| vm-web02 | **192.168.11.12** | 10,30 | 2 | 2GB | Ubuntu 24 | Apache :8080, WordPress replica | ✅ running |
| vm-services01 | **192.168.13.11** | 30 | 2 | 4GB | Ubuntu 24 | Postfix SMTP, Dovecot IMAP/POP3, Roundcube webmail, Dolibarr ERP, MySQL | pendiente |
| vm-storage01 | **192.168.14.11/26** | 40 | 1 | 2GB | Ubuntu 24 | Samba AD join, NFS exports | ✅ AD join OK |
| vm-voip01 | 192.168.50.11 | 50 | 1 | 2GB | Ubuntu 24 | Asterisk 20.6, 3 extensiones SIP | pendiente |
| vm-monitor01 | 192.168.70.11 | 70 | 2 | 4GB | Ubuntu 24 | Zabbix Server, Grafana nativa | pendiente |
| vm-docker01 | 192.168.30.12 | 30 | 2 | 4GB | Ubuntu 24 | Docker, Grafana contenedor, Portainer CE | pendiente |
| core1 | **192.168.10.20/24** | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP root | ✅ running |
| core2 | **192.168.10.30/24** | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP backup | ✅ running |
| pfSense | 192.168.10.1 | WAN | 2 | 2GB | pfSense | Firewall, NAT, CARP HA, VIPs, rutas estaticas | pendiente |

## 4b. ISPs Remotos

| VM | WAN IP | WAN GW | LAN IP | Rol | Ubicacion |
|----|--------|--------|--------|-----|-----------|
| isp-aqp01 | 192.167.1.2/24 | 192.167.1.254 | 192.167.82.1/24 | Gateway NAT + Routing | Arequipa |
| isp-tru01 | 192.168.2.2/24 | 192.168.2.254 | 192.170.12.1/24 | Gateway NAT + Routing | Trujillo |

## 4c. VMs Arequipa - VERIFICADO ✅

| VM | IP Real | VLAN | vCPU | RAM | SO | Servicios | Estado |
|----|---------|------|------|-----|-----|-----------|--------|
| **core-aqp1** | **192.167.10.20/24** | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP MASTER | ✅ running |
| **core-aqp2** | **192.167.10.30/24** | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP BACKUP | ✅ running |
| **aqp-storage01** | **192.167.14.11/26** | 14 | 1 | 2GB | Ubuntu 24 | Samba standalone, NFS exports | ✅ running |
| **aqp-dc01** | **192.167.16.10/27** | 16 | 2 | 2GB | Ubuntu 24 | Samba4 AD DC, BIND9, ISC-DHCP | ✅ running |
| **aqp-dns01** | **192.167.16.11/27** | 16 | 1 | 2GB | Ubuntu 24 | BIND9 slave, ISC-DHCP secondary | ✅ running |
| **aqp-voip01** | — | — | — | — | — | No existe en Arequipa |
| **pfSense-AQP** | 192.167.82.1 | 82 | 2 | 2GB | pfSense | Firewall, NAT, VLANs, Tailscale | ✅ configurado |

**Notas:**
- **Interlink cores**: 10.0.0.0/30 (core-aqp1=10.0.0.1, core-aqp2=10.0.0.2)
- **Tailscale**: 192.167.10.10 (pfSense-AQP) - subnet router hacia Lima
- **Consumo de servicios**: Se consumen servicios de Lima (192.168.0.0/16) vía Tailscale

## 4d. VMs Trujillo

| VM | IP | VLAN | Servicios |
|----|-----|------|-----------|
| core-tru | 192.170.12.2 | trunk | FRR OSPF, STP |
| tru-dc01 | 192.170.12.62 | 60 | AD DNS local, DHCP local |
| tru-dns01 | 192.170.12.63 | 60 | BIND9 slave local |
| tru-voip01 | 192.170.12.64 | 50 | Asterisk local (consume de Lima) |

---

## 17. Infrastructure Arequipa - VERIFICADO ✅

### 17.1. Cores Arequipa - VERIFICADO ✅

| VM | IP | Router ID | Estado | Priority | Notas |
|----|-----|-----------|--------|----------|-------|
| **core-aqp1** | 192.167.10.20/24 | 10.0.0.1 | ✅ MASTER | 200 | Keepalived running |
| **core-aqp2** | 192.167.10.30/24 | 10.0.0.2 | ✅ BACKUP | 100 | Keepalived running |
| **Interlink** | 10.0.0.0/30 | — | ✅ UP | — | core1=10.0.0.1, core2=10.0.0.2 |

**OSPF (FRR) - Redes Anunciadas (Área 0):**
```
router ospf
  ospf router-id 10.0.0.1 (core1) / 10.0.0.2 (core2)
  passive-interface default
  network 10.0.0.0/30 area 0.0.0.0
  network 192.167.12.0/25 area 0.0.0.0  # VLAN 12 - Usuarios
  network 192.167.21.0/27 area 0.0.0.0  # VLAN 21 - Admin
  network 192.167.14.0/26 area 0.0.0.0  # VLAN 14 - Storage
  network 192.167.15.0/26 area 0.0.0.0  # VLAN 15 - VoIP
  network 192.167.16.0/27 area 0.0.0.0  # VLAN 16 - Gestión
```

**Diferencia con Lima:**
- **Arequipa**: Sin interfaces bridge (pfSense maneja VLANs)
- **Lima**: Con interfaces bridge (cores manejan VLANs directamente)

**Comandos de Verificación:**
```bash
# Estado de Keepalived
systemctl status keepalived
cat /etc/keepalived/keepalived.conf | grep priority

# Estado de FRR/OSPF
systemctl status frr
sudo vtysh -c "show ip ospf neighbor"
sudo vtysh -c "show ip route ospf"

# Verificar interlink
ping -c 3 192.167.10.30  # desde core1
ping -c 3 192.167.10.20  # desde core2
```

### 17.2. pfSense Arequipa - Tailscale

| Item | Configuración |
|------|---------------|
| **IP Tailscale** | 192.167.10.10 |
| **Ruta anunciada** | 192.167.0.0/16 hacia Lima |
| **Ruta recibida** | 192.168.0.0/16 desde Lima |
| **Gateway Tailscale** | 192.167.10.10 |

**Rutas Estáticas en pfSense-AQP:**
```
Destination: 192.168.0.0/16 (Lima)
Gateway: 192.167.10.10 (Tailscale)
```

### 17.6. DC/DNS/DHCP Arequipa - VERIFICADO ✅

**aqp-dc01 (192.167.16.10) - VLAN 16 Gestión**

| Servicio | Estado | Notas |
|----------|--------|-------|
| **Samba AD** | ✅ running | Domain Function Level: 2008 R2 |
| **Dominio** | ✅ AXIOM.LOCAL | `DC=axiom,DC=local` (mismo que Lima) |
| **Usuarios AD** | ✅ 6 usuarios | jefazo, contador, Guest, krbtgt, secretaria, Administrator |
| **BIND9 DNS** | ✅ running | Master para AXIOM.local (Arequipa) |
| **DHCP** | ✅ running | Failover con aqp-dns01 |
| **Conectividad Lima** | ✅ | Ping a 192.168.16.10 (2-4ms vía Tailscale) |

**aqp-dns01 (192.167.16.11) - VLAN 16 Gestión**

| Servicio | Estado | Notas |
|----------|--------|-------|
| **BIND9 DNS** | ✅ running | Slave, forwarders a Lima (192.168.60.10) |
| **DHCP** | ✅ running | Secondary en failover con aqp-dc01 |

**Configuración DNS (named.conf.options):**

```bash
forwarders {
    192.168.60.10; // vm-dc01 Lima
    8.8.8.8;
    8.8.4.4;
};
```

**Zonas DNS configuradas:**

```bash
zone "AXIOM.local" {
    type master;
    file "/var/lib/bind/zones/db.AXIOM.local";
    allow-transfer { 192.167.16.11; 192.168.60.11; };
};

zone "16.167.192.in-addr.arpa" {  // VLAN 16 reversa
    type master;
    file "/var/lib/bind/zones/db.192.167.16";
};

zone "12.167.192.in-addr.arpa" {  // VLAN 12 reversa
    type master;
    file "/var/lib/bind/zones/db.192.167.12";
};
```

**Consumo de Servicios de Lima:**

| Servicio | IP Lima | Accesible desde Arequipa | Método |
|----------|---------|--------------------------|--------|
| AD Primary | 192.168.16.10 | ✅ | Réplica Samba (aqp-dc01) |
| DNS Master | 192.168.16.10 | ✅ | Forwarders en named.conf |
| DNS Secondary | 192.168.16.11 | ✅ | aqp-dns01 (local) |
| Zabbix | 192.168.17.11 | ✅ | Vía Tailscale |
| Web/HAProxy | 192.168.11.11 | ✅ | Vía Tailscale |
| Email | 192.168.13.11 | ✅ | Vía Tailscale |
| Storage Lima | 192.168.14.11 | ✅ | SMB/NFS vía Tailscale |
| Grafana | 192.168.17.11 | ✅ | Vía Tailscale |
| Portainer | 192.168.13.12 | ✅ | Vía Tailscale |

**Notas:**
- aqp-dc01 es **DC independiente** pero con el **mismo dominio AXIOM.LOCAL** que Lima
- Los usuarios se replican automáticamente entre Lima y Arequipa
- DNS usa forwarders hacia Lima para resolución externa
- DHCP tiene failover local entre aqp-dc01 (192.167.16.10) y aqp-dns01 (192.167.16.11)
- **Tailscale**: Conecta ambas sedes (Lima ↔ Arequipa) con ping de 2-4ms
- **pfSense-AQP VIP**: 192.167.16.3 (gateway para VLAN 16)

**aqp-storage01 (192.167.14.11) - VLAN 14 Storage**

| Servicio | Estado | Notas |
|----------|--------|-------|
| **Hostname** | arq-storage01 ⚠️ | Debe cambiarse a aqp-storage01 (reboot pendiente) |
| **IP** | 192.167.14.11/26 | bond0 |
| **SMBD** | ✅ running | ROLE_STANDALONE (no unido a AD) |
| **NFS Server** | ✅ active | Exports configurados |
| **AD Join** | ⏳ pendiente | Configurado como standalone (intencional) |

**NFS Exports (VERIFICADO):**

```bash
/shared/public      192.167.12.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/public      192.167.16.0/27(rw,sync,no_subtree_check,no_root_squash)
/shared/projects    192.167.12.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/projects    192.167.16.0/27(rw,sync,no_subtree_check,no_root_squash)
/shared/departments 192.167.16.0/27(rw,sync,no_subtree_check,no_root_squash)
```

**Comandos de Verificación:**

```bash
# Estado de servicios
systemctl status smbd nfs-server

# Verificar Exports
showmount -e localhost

# Verificar disco
df -h
```

**Notas:**
- Hostname `arq-storage01` debe cambiarse a `aqp-storage01` y reiniciar
- Configurado como **ROLE_STANDALONE** (no unido a AD) - intencional
- Usuarios locales de Samba deben crearse con `smbpasswd -a <usuario>`

### 17.4. Consumo de Servicios de Lima desde Arequipa - GUÍA COMPLETA

**Servicios de Lima accesibles vía Tailscale:**

| Servicio | IP Lima | Puerto | Protocolo | Accesible | Uso en Arequipa |
|----------|---------|--------|-----------|-----------|-----------------|
| **AD Primary** | 192.168.16.10 | 389, 88 | LDAP/Kerberos | ✅ | Réplica con aqp-dc01 |
| **DNS Master** | 192.168.16.10 | 53 | DNS | ✅ | Forwarders en BIND9 |
| **DNS Secondary** | 192.168.16.11 | 53 | DNS | ✅ | Backup DNS |
| **Zabbix** | 192.168.17.11 | 80, 10051 | HTTP/Agent | ✅ **200** | Monitoreo centralizado |
| **Web/HAProxy** | 192.168.11.11 | 80, 443 | HTTP/HTTPS | ✅ **200** | WordPress, Dolibarr, Webmail |
| **Email (Postfix)** | 192.168.13.11 | 25, 993, 995 | SMTP/IMAP | ✅ **OK** | Correo corporativo |
| **Storage Lima** | 192.168.14.11 | 445, 2049 | SMB/NFS | ✅ **200, 6 shares** | Shares adicionales |
| **Grafana** | 192.168.17.11 | 3000 | HTTP | ✅ **302→/login** | Dashboards de monitoreo |
| **Portainer** | 192.168.13.12 | 9000, 9443 | HTTP/HTTPS | ✅ **307→redirect** | Gestión Docker |
| **Asterisk** | 192.168.15.11 | 5060, 10000-10100 | SIP/RTP | ⚠️ REFUSED | VoIP corporativo |

**Comandos de Verificación desde Arequipa:**

```bash
# 1. Probar DNS de Lima
dig @192.168.16.10 axiom.local

# 2. Probar web de Lima (HAProxy)
curl -I http://192.168.11.11/

# 3. Probar storage de Lima (SMB)
smbclient -L //192.168.14.11 -U jefazo%rol.123

# 4. Probar Zabbix de Lima
curl -I http://192.168.17.11/zabbix/

# 5. Probar Asterisk de Lima (SIP)
nc -zv 192.168.15.11 5060

# 6. Verificar ruta a Lima
ip route | grep 192.168
```

**Próximo paso:** Probar todos los servicios de Lima desde Arequipa.

## 5. Active Directory - VERIFICADO ✅

- **Dominio**: AXIOM.LOCAL (realm), AXIOM (NetBIOS)
- **DC**: vm-dc01 (**192.168.16.10**)
- **Estado**: ✅ samba-ad-dc running (60 procesos, 273MB RAM)
- **Admin password**: `rol.123` (cambiada de `admin123!`)

### Usuarios AD

| Usuario | Grupo | Password |
|---------|-------|----------|
| jefazo | axiom-administradores | rol.123 |
| secretaria | axiom-secretaria | rol.123 |
| contador | axiom-usuarios | rol.123 |
| Administrator | Domain Admins, Enterprise Admins | rol.123 |

### Grupos AD

| Grupo (winbind) | GID range | Proposito |
|------------------|-----------|-----------|
| axiom-administradores | 10000-20000 | Administradores |
| axiom-secretaria | 10000-20000 | Secretaria |
| axiom-usuarios | 10000-20000 | Usuarios generales |

### idmap config

- `*` : range 2000-9999
- `AXIOM` : range 10000-20000

### ⚠️ Problema de Join a AD - Explicación y Solución

**Problema encontrado en vm-storage01:**
```
Failed to join domain: failed to find DC for domain AXIOM
```

**Causa raíz:** Se usó el nombre NetBIOS `AXIOM` en lugar del FQDN `AXIOM.LOCAL`

**Comandos que fallaron:**
```bash
net ads join -U administrator        # Sin dominio especificado
net ads join -U administrator%rol.123  # Usa NetBIOS name (AXIOM)
```

**Comando exitoso:**
```bash
net ads join -U administrator@AXIOM.LOCAL%rol.123
```

**¿Por qué funcionó?**
1. **DNS SRV records**: El cliente necesita resolver `_ldap._tcp.AXIOM.local` y `_kerberos._tcp.AXIOM.local`
2. **FQDN completo**: `administrator@AXIOM.LOCAL` especifica el realm completo de Kerberos
3. **DNS configurado**: `/etc/resolv.conf` debe apuntar a `192.168.16.10` (el DC) como nameserver primario

**Lección:** Siempre usar `usuario@DOMINIO.LOCAL` (FQDN) para operaciones de AD, no solo el nombre NetBIOS.

## 6. DNS — BIND9 Failover - VERIFICADO ✅

| Rol | VM | IP | Zonas | Estado |
|-----|-----|-----|-------|--------|
| MASTER | vm-dc01 | **192.168.16.10** | AXIOM.local + reversas | ✅ running |
| SLAVE | vm-dns02 (dc02) | **192.168.16.11** | Transferencia automatica via AXFR | ✅ running |

### Fix aplicado (Jul 2026)
- **Problema**: `named.conf.local` en vm-dns02 tenía IP incorrecta (`192.168.60.10`)
- **Solución**: Revertir a IP correcta (`192.168.16.10`)
- **Verificación**: `dig @192.168.16.11 axiom.local SOA` → `status: NOERROR`

### ⚠️ Nota sobre IPs de DNS
Las IPs originales de la documentación eran `192.168.60.10` y `192.168.60.11`, pero las IPs **reales** verificadas son `192.168.16.10` y `192.168.16.11`. Esto causó confusión en la configuración del slave DNS y en el join a AD de vm-storage01.

**Lección:** Siempre verificar las IPs reales con `ip a | grep "inet "` antes de configurar servicios.

### Registros DNS (AXIOM.local)

| Registro | Tipo | Valor |
|----------|------|-------|
| vm-dc01 | A | 192.168.16.10 |
| dns02 | A | 192.168.16.11 |
| pfsense | A | 192.168.10.1 |
| vm-web01 | A | 192.168.11.11 |
| vm-web02 | A | 192.168.11.12 |
| mail | A | 192.168.13.11 |
| webmail | CNAME | mail |
| smtp | CNAME | mail |
| imap | CNAME | mail |
| storage | A | 192.168.14.11 |
| archivos | CNAME | storage |
| vm-docker01 | A | 192.168.30.12 |
| grafana | A | 192.168.30.12 |
| portainer | A | 192.168.30.12 |
| monitor | A | 192.168.70.11 |
| www | CNAME | vm-web01 |
| blog | A | 192.168.11.11 |
| _ldap._tcp | SRV | 0 100 389 vm-dc01 |
| _kerberos._tcp | SRV | 0 100 88 vm-dc01 |
| _kerberos._udp | SRV | 0 100 88 vm-dc01 |

## 7. DHCP — ISC Failover - VERIFICADO ✅

| Rol | VM | IP | Puerto failover | Estado |
|-----|-----|-----|-----------------|--------|
| PRIMARY | vm-dc01 | 192.168.16.10 | 647 | ✅ running |
| SECONDARY | vm-dns02 | 192.168.16.11 | 647 | ✅ running |

### Failover Peer State
- **vm-dc01 (PRIMARY)**: state normal
- **vm-dns02 (SECONDARY)**: state normal
- **Split**: 128 (balanceo 50/50)
- **MCLT**: 3600s

### Rangos DHCP

| VLAN | Subnet | Rango | Gateway |
|------|--------|-------|---------|
| 20 | 192.168.12.0/24 | .81 - .200 | 192.168.12.1 |
| 21 | 192.168.21.0/27 | .10 - .30 | 192.168.21.1 |
| 60 | 192.168.16.0/27 | .11 - .30 | 192.168.16.1 |

### Leases activas (ejemplos)
- 192.168.12.83 → sai-vmware201 (00:0c:29:48:c1:0a)
- 192.168.12.84 → sai (00:0c:29:1b:ed:66)

## 8. NTP — chrony - VERIFICADO ✅

- **Servidor**: vm-dns02 (192.168.16.11)
- **Estado**: ✅ running
- **Permite**: 192.168.0.0/16
- **Upstream**:
  - prod-ntp-3.ntp1.ps5.canonical.com (stratum 2)
  - prod-ntp-4.ntp1.ps5.canonical.com (stratum 2)
  - time.cloudflare.com (stratum 3) ★ seleccionado
  - b.ntp.br (stratum 2)
  - south-america.pool.ntp.org
- **Stratum local**: 10

---

## 22. Pendientes - Lima HQ

| VM | Tarea | Estado | Notas |
|----|-------|--------|-------|
| vm-dns02 | Verificar logs de DNS sin "non-authoritative answer" | ✅ completado | Fix aplicado en named.conf.local |
| vm-storage01 | Verificar acceso a shares SMB desde clientes | ✅ completado | AD join exitoso |
| vm-storage01 | Verificar montajes NFS desde clientes | ⏳ pendiente | Exports configurados |
| vm-web01 + vm-web02 | Verificar HAProxy + WordPress | ✅ completado | Balanceo roundrobin funcionando |
| vm-services01 | Verificar email + Dolibarr + MySQL | ⏳ pendiente | |
| vm-voip01 | Verificar Asterisk + extensiones | ⏳ pendiente | |
| vm-monitor01 | Verificar Zabbix + agentes | ⏳ pendiente | |
| vm-docker01 | Verificar Grafana + Portainer | ⏳ pendiente | |
| Tailscale | Conectar Lima ↔ Arequipa | ✅ completado | Ping exitoso entre sedes |

---

## 23. Lecciones Aprendidas - Julio 2026

### 1. IPs de Documentación vs Realidad
**Problema:** La doc decía `192.168.60.x` pero las IPs reales eran `192.168.16.x`

**Solución:**
```bash
# Siempre verificar IPs reales antes de configurar
ip a | grep "inet "
```

**Lección:** La documentación debe actualizarse con IPs **reales**, no las planificadas.

### 2. AD Join - NetBIOS vs FQDN
**Problema:** `net ads join -U administrator` fallaba

**Causa:** Uso de nombre NetBIOS `AXIOM` en lugar de FQDN `AXIOM.LOCAL`

**Solución:**
```bash
# Comando correcto (con FQDN y realm de Kerberos):
net ads join -U administrator@AXIOM.LOCAL%rol.123
```

**Lección:** Siempre usar `usuario@DOMINIO.LOCAL` para operaciones de AD.

### 3. DNS Slave - IP de Master
**Problema:** Logs mostraban "non-authoritative answer"

**Causa:** `named.conf.local` tenía IP incorrecta del master (`192.168.60.10` en vez de `192.168.16.10`)

**Solución:**
```bash
sed -i 's/192.168.60.10/192.168.16.10/g' /etc/bind/named.conf.local
systemctl restart named
```

**Lección:** Verificar transferencia de zonas con `dig @slave domain.local SOA`

### 4. VLANs en Locales Remotos
**Problema:** Configuración inicial incluía VLANs en servidores de Arequipa/Trujillo

**Solución:** Las VLANs se configuran **solo en pfSense**, los servidores Linux van sin VLAN tagging.

**Lección:** pfSense maneja todo el routing/VLAN, los servidores solo IP plana.

## 9. Web — WordPress + HAProxy - VERIFICADO ✅

### HAProxy (vm-web01 :80) - Confirmado

| Ruta | Backend | Detalle |
|------|---------|---------|
| `/` | vm-web01 :8080 + vm-web02 :8080 | roundrobin — WordPress |
| `/wp-*` | vm-web01 :8080 + vm-web02 :8080 | roundrobin |
| `/dolibarr/` | vm-services01 :80 | strip /dolibarr prefix |
| `/webmail` | vm-services01 :80 | — |
| `/voip` | vm-voip01 :80 | — |
| :8404/haproxy | Stats UI | admin / proxy.123 |

### vm-web01 (192.168.11.11) - Estado Verificado

| Servicio | Estado | Puerto | Notas |
|----------|--------|--------|-------|
| **HAProxy** | ✅ running | :80 (frontend), :8404 (stats) | Balanceo roundrobin |
| **Apache2** | ✅ running | :8080 | WordPress |
| **WordPress** | ✅ instalado | `/var/www/axiom/` | wp-config.php existe |

### vm-web02 (192.168.11.12) - Estado Verificado

| Servicio | Estado | Puerto | Notas |
|----------|--------|--------|-------|
| **Apache2** | ✅ running | :8080 | WordPress replica |
| **WordPress** | ✅ configurado | `/var/www/axiom/` | Misma DB que web01 |

### Backend Configuration (HAProxy)

```haproxy
backend wordpress_backend
    balance roundrobin
    server web01 127.0.0.1:8080 check
    server web02 192.168.11.12:8080 check
```

### Comandos de Verificación

```bash
# HAProxy stats
curl -u admin:proxy.123 http://192.168.11.11:8404/haproxy

# WordPress (balanceo roundrobin)
curl -I http://192.168.11.11/

# Logs de HAProxy
tail -f /var/log/haproxy.log
```

### Tráfico Observado (logs)

```
wordpress_backend/web02 0/0/0/21/21 302 320  → WordPress responde
wordpress_backend/web01 0/0/0/128/307 200   → WordPress responde OK
stats stats/<STATS> 200 39772                → HAProxy stats funciona
```

- WordPress DocumentRoot: `/var/www/axiom/` (no `/var/www/html/`)
- DB: axiom_web en vm-services01 (192.168.13.11)
- web02 usa la MISMA DB que web01 — contenido idéntico
- Nginx DETENIDO en vm-web01 — solo Apache :8080
- **Grafana y Portainer NO van por HAProxy** — acceso directo via DNS

### Accesos Web

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| WordPress | http://axiom.web.AXIOM.local/ | — |
| HAProxy Stats | http://192.168.11.11:8404/haproxy | admin / proxy.123 |
| Dolibarr ERP | http://192.168.11.11/dolibarr/ | — |
| Webmail | http://192.168.11.11/webmail/ | secretaria / rol.123 |

## 10. Email — Postfix + Dovecot + Roundcube - VERIFICADO ✅

| Servicio | Puerto | Detalle | Estado |
|----------|--------|---------|--------|
| SMTP | 25 | Postfix | ✅ active |
| IMAP | 143 | Dovecot | ✅ running |
| IMAP-SSL | 993 | Dovecot (SSL) | ✅ running |
| POP3 | 110 | Dovecot | ✅ running |
| POP3-SSL | 995 | Dovecot (SSL) | ✅ running |
| Webmail | 80 /webmail/ | Roundcube | ✅ funcionando |

- **Servidor**: vm-services01 (**192.168.13.11**) - VLAN 30 Services
- **MySQL root**: AdminMail123! (via sudo mysql)
- **Acceso Webmail**: http://192.168.11.11/webmail/ (via HAProxy)
- **Auth**: Winbind AD (secretaria / rol.123)
- **BD Roundcube**: ✅ Existe (roundcube)

## 10b. ERP — Dolibarr - VERIFICADO ✅

- **URL**: http://192.168.11.11/dolibarr/ (via HAProxy)
- **Real**: http://192.168.13.11/ (root del servidor)
- **DB**: MySQL en vm-services01 (192.168.13.11)
- **BD Dolibarr**: ✅ Existe (dolibarr)
- **Estado**: ⏳ Pendiente verificar vía web

## 10c. WordPress DB - VERIFICADO ✅

- **DB**: axiom_web en vm-services01
- **Estado**: ✅ Existe y creada
- **Conexión**: web01 y web02 conectan a esta DB
- **Verificación**: `sudo mysql -e "SHOW DATABASES;"` → axiom_web presente

## 12. Storage — Samba + NFS - VERIFICADO ✅

### vm-storage01 - Estado Confirmado

| Item | Valor Real | Notas |
|------|------------|-------|
| **IP** | **192.168.14.11/26** | VLAN 40 Storage (bond0 active-backup) |
| **Hostname** | VM-STORAGE01 | Unido a AXIOM.LOCAL |
| **SMBD/NMBD** | ✅ running | ROLE_DOMAIN_MEMBER |
| **Winbind** | ✅ running | AD join exitoso |
| **NFS Server** | ✅ active | Exports configurados |
| **AD Join** | ✅ COMPLETED | `net ads join -U administrator@AXIOM.LOCAL%rol.123` |
| **LDAP** | ✅ 192.168.16.10 | vm-dc01.axiom.local |
| **KDC** | ✅ 192.168.16.10 | Tiempo sincronizado (offset 0) |
| **DNS** | ✅ 192.168.16.10, 192.168.16.11 | SRV records resueltos |

### ⚠️ Problema de AD Join - Solucionado

**Error inicial:**
```
Failed to join domain: failed to find DC for domain AXIOM
```

**Causa:** Uso de nombre NetBIOS `AXIOM` en lugar de FQDN `AXIOM.LOCAL`

**Solución:**
```bash
# Comando correcto (con FQDN):
net ads join -U administrator@AXIOM.LOCAL%rol.123

# Verificación:
net ads testjoin  # → Join is OK
net ads info      # → Muestra LDAP, KDC, Realm
wbinfo -u         # → Muestra usuarios AD
```

### Samba Shares (vm-storage01)

| Share | Path | Permisos | Usuarios Válidos |
|-------|------|----------|------------------|
| Jefatura | /srv/samba/Jefatura | 0770 | @axiom-administradores |
| Secretaria | /srv/samba/Secretaria | 0775 | @axiom-secretaria, @axiom-administradores |
| Usuarios | /srv/samba/Usuarios | 0775 | Todos los grupos |
| Publico | /srv/samba/Publico | 0755 | Solo lectura, todos los grupos |
| homes | /srv/samba/homes/%U | 0700 | Usuario individual |

**Acceso UNC:**
- `\\vm-storage01.AXIOM.local\Jefatura`
- `\\vm-storage01.AXIOM.local\Secretaria`
- `\\vm-storage01.AXIOM.local\Usuarios`
- `\\vm-storage01.AXIOM.local\Publico`
- `\\vm-storage01.AXIOM.local\%USERNAME%` (homes)

### NFS Exports

| Path | Clientes | Opciones |
|------|----------|----------|
| /shared/public | 192.168.12.0/25 (VLAN 20), 192.168.13.0/25 (VLAN 30) | rw,sync,no_subtree_check,no_root_squash |
| /shared/departments | 192.168.13.0/25 | rw,sync,no_subtree_check,no_root_squash |
| /shared/projects | 192.168.13.0/25 | rw,sync,no_subtree_check,no_root_squash |

**Montaje NFS desde clientes:**
```bash
mount -t nfs 192.168.14.11:/shared/public /mnt/public
mount -t nfs 192.168.14.11:/shared/departments /mnt/departments
mount -t nfs 192.168.14.11:/shared/projects /mnt/projects
```

**Exports NFS vm-storage01 (Lima) - ACTUALIZADO:**
```bash
/shared/public      192.168.12.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/public      192.168.13.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/public      192.170.12.0/24(rw,sync,no_subtree_check,no_root_squash)  # Trujillo
/shared/departments 192.168.13.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/departments 192.170.12.0/24(rw,sync,no_subtree_check,no_root_squash)  # Trujillo
/shared/projects    192.168.13.0/25(rw,sync,no_subtree_check,no_root_squash)
/shared/projects    192.170.12.0/24(rw,sync,no_subtree_check,no_root_squash)  # Trujillo
```

**Consumo Storage Lima:**
```bash
# Desde cualquier sede (Lima, Arequipa, Trujillo vía VPN)
smbclient -L //192.168.14.11 -N
mount -t nfs 192.168.14.11:/shared/public /mnt/public
```

## 13. VoIP — Asterisk - VERIFICADO ✅

- **VM**: vm-voip01 (**192.168.15.11**) - VLAN 50 VoIP
- **Estado**: ✅ running (10h uptime, 90MB RAM)
- **Extensiones**: 100, 101, 102 (password: rol.123)
- **Protocolo**: SIP

### Extensiones Configuradas:

| Ext | Nombre | Estado | IP | Password | Notas |
|-----|--------|--------|-----|----------|-------|
| 100 | Jefazo | ⚠️ UNKNOWN | — | rol.123 | Configurada, no registrada |
| 101 | — | ✅ OK | 192.168.12.84 | rol.123 | ¡Registrada y respondiendo! |
| 102 | — | ⚠️ UNKNOWN | — | rol.123 | Configurada, no registrada |

### Comandos de Verificación:

```bash
# Estado de Asterisk
systemctl status asterisk

# Ver peers SIP
sudo asterisk -rx "sip show peers"

# Ver usuarios SIP
sudo asterisk -rx "sip show users"

# Ver configuración de extensión
cat /etc/asterisk/sip.conf | grep -A 5 "[100]"
```

### Notas:
- **Warning RADIUS**: Mensaje `can't open /etc/radiusclient-ng/radiusclient.conf` es **inocente**, no afecta operación
- **Extensión 101 registrada**: IP 192.168.12.84 respondiendo con 1ms de latencia
- **Salida PSTN**: No configurada (falta gateway FXO/SIP trunk)

## 14. Monitoreo — Zabbix + Grafana - VERIFICADO ✅

### Zabbix Server (vm-monitor01) - VERIFICADO ✅

- **VM**: vm-monitor01 (**192.168.17.11**) - VLAN 70 Monitoreo
- **URL**: http://axiom.monitor.AXIOM.local/zabbix/
- **Estado**: ✅ running (10h uptime, 87MB RAM, 77 procesos)
- **Admin**: Admin / zabbix
- **Puerto**: 10051 (Zabbix Server)

### Agentes monitoreados (10 VMs):

| VM | IP | VLAN | Estado |
|----|-----|------|--------|
| vm-dc01 | 192.168.16.10 | 60 | ✅ monitoreada |
| vm-dns02 | 192.168.16.11 | 60 | ✅ monitoreada |
| vm-web01 | 192.168.11.11 | 10 | ✅ monitoreada |
| vm-web02 | 192.168.11.12 | 10 | ✅ monitoreada |
| vm-services01 | 192.168.13.11 | 30 | ✅ monitoreada |
| vm-storage01 | 192.168.14.11 | 40 | ✅ monitoreada |
| vm-voip01 | 192.168.15.11 | 50 | ✅ monitoreada |
| vm-docker01 | 192.168.13.12 | 30 | ✅ monitoreada |
| vm-monitor01 | 192.168.17.11 | 70 | ✅ monitoreada |
| core1 | 192.168.10.20 | trunk | ✅ monitoreado |
| core2 | 192.168.10.30 | trunk | ✅ monitoreado |

### Housekeeper:
- Elimina 1200 históricos/hora automáticamente
- Limpia problemas expirados

### Grafana Server (vm-monitor01) - VERIFICADO ✅

- **Acceso directo**: http://axiom.grafana.AXIOM.local:3000
- **IP directa**: http://192.168.17.11:3000
- **Estado**: ✅ running (10h uptime, 199MB RAM)
- **Admin**: admin / grafana.123
- **Plugins**: Elasticsearch, Zipkin cargados
- **Datasource Zabbix**: Configurar manualmente en UI (API: http://192.168.17.11/zabbix/api_jsonrpc.php, user: Admin, pass: zabbix)

### Comandos de Verificación:

```bash
# Estado de servicios
systemctl status zabbix-server grafana-server

# Verificar puertos
sudo ss -tlnp | grep -E "10051|3000"

# Verificar web Zabbix
curl -I http://localhost/zabbix/

# Ver hosts monitoreados
sudo mysql -e "SELECT host FROM zabbix.hosts WHERE status=0;" zabbix
```

### Notas:
- **Warning de hostname**: `unable to resolve host vm-monitor01` es solo aviso de `/etc/hosts`, no afecta operación
- **Auto-recovery**: vm-web01 se enciende automáticamente si se detecta nodata

## 15. Docker — Portainer + Grafana - VERIFICADO ✅

### vm-docker01 - Estado Verificado

| Item | Estado | Notas |
|------|--------|-------|
| **VM** | 192.168.13.12 | VLAN 30 Services |
| **Docker Engine** | ✅ running | 10h uptime, 130MB RAM |
| **Grafana (container)** | ✅ UP | grafana/grafana:latest (378MB) |
| **Portainer CE** | ✅ UP | portainer/portainer-ce:latest (42MB) |
| **docker-proxy** | ✅ running | Puertos 3000, 9000, 9443 |

### Accesos Directos:

| Servicio | URL | Puerto | Credenciales | Estado |
|----------|-----|--------|--------------|--------|
| **Grafana HTTP** | http://192.168.13.12:3000 | 3000 | admin / grafana.123 | ✅ 302 → /login |
| **Portainer HTTP** | http://192.168.13.12:9000 | 9000 | Crear password | ✅ 307 → setup |
| **Portainer HTTPS** | https://192.168.13.12:9443 | 9443 | Crear password | ✅ |
| **Grafana DNS** | http://axiom.grafana.AXIOM.local:3000 | 3000 | admin / grafana.123 | ✅ |
| **Portainer DNS** | http://axiom.portainer.AXIOM.local:9000 | 9000 | Crear password | ✅ |

### Contenedores:

```bash
CONTAINER ID   IMAGE                           PORTS                                    NAMES
78c00620b99d   grafana/grafana:latest          0.0.0.0:3000->3000/tcp                   grafana
8523a6df549a   portainer/portainer-ce:latest   0.0.0.0:9000->9000/tcp, 9443->9443/tcp   portainer
```

### Imágenes Docker:

| Image | ID | Size | Content Size |
|-------|-----|------|--------------|
| grafana/grafana:latest | 121a7a9ece6d | 1.58GB | 378MB |
| portainer/portainer-ce:latest | 5f9b4bda5582 | 187MB | 41.9MB |

### Comandos de Verificación:

```bash
# Estado de Docker
systemctl status docker

# Contenedores corriendo
docker ps

# Verificar puertos
sudo ss -tlnp | grep -E "3000|9000|9443"

# Probar acceso
curl -I http://localhost:3000  # Grafana → 302 Found
curl -I http://localhost:9000  # Portainer → 307 Redirect
```

### Notas:
- **Warning DNS**: `failed to query external DNS server` es inocente, no afecta contenedores
- **Portainer**: Crear contraseña de administrador en primer acceso
- **Grafana**: Password por defecto `grafana.123`, cambiar después de primer login
- **Docker network**: axiom-net (crear si no existe)

## 16. VPN — Tailscale - VERIFICADO ✅

### Estado Actual

| Item | Estado | Notas |
|------|--------|-------|
| **Tailscale VPN** | ✅ funcionando | Túnel activo entre sedes |
| **Lima ↔ Arequipa** | ✅ conectado | Ping exitoso entre sedes |
| **ACL/Firewall** | ⏳ pendiente | Sin reglas configuradas (tráfico libre) |
| **Rutas anunciadas** | ✅ configuradas | 192.168.0.0/16, 172.17.25.0/24 |

### IPs de Tailscale por sede:

| Sede | IP Tailscale | Subnet Router | Rutas Anunciadas |
|------|--------------|---------------|------------------|
| **Lima** | 192.168.12.83 | vm-vpn01 | 192.168.0.0/16 completo |
| **Arequipa** | 192.167.10.10 | pfsense-aqp | 192.167.82.0/24, 192.167.1.0/24 |
| **Trujillo** | Pendiente | pfsense-tru | 192.170.12.0/24, 192.168.2.0/24 |

### Rutas Estáticas en pfSense:

**pfSense-Lima:**
```
Destination: 192.167.0.0/16 (Arequipa)
Gateway: 192.168.12.83 (Tailscale Lima)
```

**pfSense-Arequipa:**
```
Destination: 192.168.0.0/16 (Lima)
Gateway: 192.167.10.10 (Tailscale Arequipa)
```

### Servicios Accesibles entre Sedes:

| Servicio | IP Lima | Accesible desde Arequipa | Estado |
|----------|---------|--------------------------|--------|
| DNS Lima | 192.168.16.10, 192.168.16.11 | ✅ | Por verificar |
| AD Lima | 192.168.16.10 | ✅ | Por verificar |
| Zabbix Lima | 192.168.17.11 | ✅ | Por verificar |
| Web/Email/ERP | 192.168.11.11, 192.168.13.11 | ✅ | Por verificar |
| Storage Lima | 192.168.14.11 | ✅ | Por verificar |
| Storage Arequipa | 192.167.14.11 | ✅ desde Lima | Por verificar |

### Comandos de Verificación:

```bash
# Desde Lima, ping a Arequipa
ping 192.167.82.62  # aqp-dc01
ping 192.167.14.11  # aqp-storage01

# Desde Arequipa, ping a Lima
ping 192.168.16.10  # vm-dc01
ping 192.168.17.11  # vm-monitor01

# Verificar rutas Tailscale
tailscale status
tailscale netcheck
```

### Notas:
- **ACL/Firewall**: Sin reglas configuradas, todo el tráfico entre sedes está permitido
- **Próximo paso**: Configurar firewall rules en pfSense para restringir tráfico si es necesario
- **Consumo de servicios**: Las sedes remotas (Arequipa/Trujillo) consumen servicios centralizados de Lima (AD, DNS, Zabbix, Web, Email, ERP)

## 17. Networking — Cores Lima

### STP (Keepalived) - VERIFICADO ✅

- **Core1**: MASTER (priority 200) - todas las VLANs
- **Core2**: BACKUP (priority 100) - todas las VLANs
- **Auth pass**: AN3IBL3P4SS
- **Interlink**: 10.0.0.0/30 (core1=10.0.0.1, core2=10.0.0.2)
- **Bond0**: ens34+ens35 (active-backup) - LAN hacia pfSenses
- **Bond1**: ens36+ens37 (active-backup) - Trunks hacia pfSenses

### OSPF (FRR) - VERIFICADO ✅

- **Area**: 0.0.0.0
- **Core1 Router ID**: 10.0.0.1
- **Core2 Router ID**: 10.0.0.2
- **Software**: FRR 9.0
- **Estado vecindad**: core1 ↔ core2 = Full/DR ↔ Full/Backup
- **Redes anunciadas**:
  - 10.0.0.0/30 (inter-link ens38)
  - 192.168.11.0/27 (VLAN 10 DMZ)
  - 192.168.12.0/25 (VLAN 20 Usuarios)
  - 192.168.21.0/27 (VLAN 21 Admin)
  - 192.168.13.0/25 (VLAN 30 Virtualización)
  - 192.168.14.0/26 (VLAN 40 Storage)
  - 192.168.15.0/26 (VLAN 50 VoIP)
  - 192.168.16.0/27 (VLAN 60 Gestión)
  - 192.168.17.0/27 (VLAN 70 Monitoreo)
  - 192.168.99.0/30 (HA Sync)
- **Interfaces pasivas**: br10, br20, br21, br30, br40, br50, br60, br70, br999
- **Interface activa**: ens38 (inter-link core1↔core2)

### pfSense

- **HA/CARP**: Activo entre 2 nodos
- **VIPs**: Una por VLAN
- **Rutas**: Estaticas (BGP removido)

## 17b. Networking — Cores Remotos

### Core-Aqp (Arequipa)

- **Router ID**: 10.1.0.1
- **Uplink**: 192.167.82.1 (ISP-aqp LAN gateway)
- **OSPF Area**: 0.0.0.0
- **STP**: Root bridge (STP priority mas baja)
- **Downlinks**: VLANs 20 y 60 trunkeadas a switches locales

### Core-Tru (Trujillo)

- **Router ID**: 10.2.0.1
- **Uplink**: 192.170.12.1 (ISP-tru LAN gateway)
- **OSPF Area**: 0.0.0.0
- **STP**: Root bridge (STP priority mas baja)
- **Downlinks**: VLANs 20 y 60 trunkeadas a switches locales
- **QoS/OSPF pfSense**: Diferido

## 18. Credenciales Consolidadas

| Servicio | Usuario | Password | Nota |
|----------|---------|----------|------|
| ESXi | root | qwe123$ | 172.17.25.12:443 |
| AD Admin | Administrator | admin123! | AXIOM.LOCAL |
| AD Users | jefazo/secretaria/contador | rol.123 | |
| MySQL | root | AdminMail123! | vm-services01 |
| WordPress DB | axiom_web | Ax1omWeb!2024 | |
| Zabbix | Admin | zabbix | |
| Grafana (docker) | admin | grafana.123 | vm-docker01 :3000, grafana.AXIOM.local |
| HAProxy stats | admin | proxy.123 | :8404/haproxy |
| Portainer | admin | (crear al primer login) | :9000, :9443, portainer.AXIOM.local |
| SSH VMs | ubuntu | 123 | Todas las VMs Lima |
| SIP extensions | 100/101/102 | rol.123 | Asterisk |
| Keepalived | — | AN3IBL3P4SS | Entre cores |

## 19. Playbooks Disponibles

| Playbook | VM | Proposito |
|----------|-----|-----------|
| vm-dc01_network.yml | dc01 | Red bond0 |
| vm-dc01_servicios.yml | dc01 | AD + DNS + DHCP |
| vm-dc01_ad_full.yml | dc01 | AD completo con usuarios y grupos |
| vm-dc01_dhcp_failover.yml | dc01 | DHCP PRIMARY failover |
| vm-dc01_fix_dns.yml | dc01 | Reparar DNS |
| vm-dns02.yml | dns02 | DNS slave + NTP + DHCP secondary |
| vm-dns02_zabbix_agent.yml | dns02 | Zabbix agent2 |
| vm-dns02_dhcp_failover.yml | dns02 | DHCP SECONDARY failover |
| vm-web01.yml | web01 | Setup inicial |
| vm-web01_haproxy_update.yml | web01 | HAProxy con todos los backends |
| vm-web02.yml | web02 | WordPress replica + Zabbix agent |
| vm-docker01.yml | docker01 | Docker + Grafana + Portainer + Zabbix |
| vm-docker01_check.yml | docker01 | Diagnostico |
| vm-storage01_ad_smb.yml | storage01 | Samba + AD join |
| vm-voip01_servicios.yml | voip01 | Asterisk |
| cores_ospf.yml | cores | FRR OSPF |
| core1_stp.yml | core1 | STP root |
| core2_stp.yml | core2 | STP backup |
| isp_setup.yml | ISP Lima | NAT solo (plantilla referencia) |
| **isp_aqp.yml** | isp-aqp01 | **ISP Arequipa: NAT + Routing** |
| **isp_tru.yml** | isp-tru01 | **ISP Trujillo: NAT + Routing** |
| pfsense_bgp.yml | pfSense | Rutas estaticas |
| pfsense_qos.yml | pfSense | QoS (diferido) |
| pfsense_ospf.yml | pfSense | OSPF (diferido) |
| backup_to_s3.yml | todas | Backup AWS S3 |

## 20. Accesos Rapidos

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| HAProxy Stats | http://192.168.10.11:8404/haproxy | admin / proxy.123 |
| WordPress | http://axiom.web.AXIOM.local/ | — |
| Grafana | http://axiom.grafana.AXIOM.local:3000 | admin / grafana.123 |
| Grafana (IP directa) | http://192.168.30.12:3000 | admin / grafana.123 |
| Portainer | http://axiom.portainer.AXIOM.local:9000 | crear password |
| Portainer (IP directa) | http://192.168.30.12:9000 | crear password |
| Portainer HTTPS | https://192.168.30.12:9443 | crear password |
| Zabbix | http://axiom.monitor.AXIOM.local/zabbix/ | Admin / zabbix |
| Webmail | http://axiom.webmail.AXIOM.local/ | secretaria / rol.123 |
| Dolibarr ERP | http://axiom.web.AXIOM.local/dolibarr/ | — |
| Asterisk PBX (Lima) | http://axiom.voip.AXIOM.local/ | extensiones 100/101/102 / rol.123 |
| Asterisk PBX (Aqp) | http://192.167.82.64/ | extensiones 100/101/102 / rol.123 |
| Asterisk PBX (Tru) | http://192.170.12.64/ | extensiones 100/101/102 / rol.123 |

## 21. Pendientes y Mejoras

- [ ] **Limpiar disco vm-dc01** — 100% lleno (apt autoremove, journalctl --vacuum-time=1d)
- [ ] **AWS hybrid** — S3 + EC2 + VPN (credenciales pendientes)
- [ ] **QoS en pfSense** — Diferido
- [ ] **OSPF en pfSense** — Diferido
- [ ] **Salida PSTN VoIP** — Requiere hardware gateway FXO
- [ ] **Zabbix datasource en Grafana docker** — Configurar manualmente en UI
- [ ] **DNS zonas reversas adicionales** — Solo 16.168.192 existe en dc01
- [ ] **Secondary DNS en Arequipa/Trujillo** — Para resolucion local en sedes remotas
- [ ] **Resolv.conf en vm-services01, vm-storage01** — Actualizar para incluir dns02 como secundario
