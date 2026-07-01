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
 192.167.82.1/24                  192.169.92.1/24
        |                               |
   [core-aqp]                     [core-tru]
   OSPF/STP                       OSPF/STP
        |                               |
   +----+----+                   +----+----+
   |           |                   |           |
SEDE AREQUIPA              SEDE TRUJILLO
192.167.82.0/24            192.169.92.0/24
        |                               |
   [Tailscale VPN 192.168.0.0/16, 172.17.25.0/24]
        |
   [pfSense HA — Lima HQ]
    CARP VIPs 192.168.x.1
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

### LIMA (HQ) — 192.168.x.x

| VLAN ID | Nombre | Subnet | Gateway | Rango IPs fijas |
|---------|--------|--------|---------|-----------------|
| 10 | DMZ | 192.168.10.0/27 | 192.168.10.1 | .10 - .30 |
| 20 | Usuarios | 192.168.20.0/24 | 192.168.20.1 | .10 - .254 |
| 21 | Administracion | 192.168.21.0/27 | 192.168.21.1 | .10 - .30 |
| 30 | Virtualizacion | 192.168.30.0/25 | 192.168.30.1 | .10 - .125 |
| 40 | Storage | 192.168.40.0/26 | 192.168.40.1 | .10 - .62 |
| 50 | VoIP | 192.168.50.0/26 | 192.168.50.1 | .10 - .62 |
| 60 | Gestion | 192.168.60.0/27 | 192.168.60.1 | .10 - .30 |
| 70 | Monitoreo | 192.168.70.0/27 | 192.168.70.1 | .10 - .30 |
| 999 | HA Sync | 192.168.99.0/30 | — | .1 - .2 |

### AREQUIPA — 192.167.82.x

| VLAN ID | Nombre | Subnet | Gateway | Notas |
|---------|--------|--------|---------|-------|
| 20 | Usuarios | 192.167.82.0/24 | 192.167.82.1 | DHCP local |
| 60 | Gestion | 192.167.82.60/28 | 192.167.82.61 | DC, DNS, VoIP local |

### TRUJILLO — 192.169.92.x

| VLAN ID | Nombre | Subnet | Gateway | Notas |
|---------|--------|--------|---------|-------|
| 20 | Usuarios | 192.169.92.0/24 | 192.169.92.1 | DHCP local |
| 60 | Gestion | 192.169.92.60/28 | 192.169.92.61 | DC, DNS, VoIP local |

## 4. Maquinas Virtuales — Lima (HQ)

| VM | IP | VLAN | vCPU | RAM | SO | Servicios |
|----|-----|------|------|-----|-----|-----------|
| vm-dc01 | 192.168.60.10 | 60 | 2 | 2GB | Ubuntu 24 | Samba4 AD DC, BIND9 master, ISC-DHCP primary |
| vm-dns02 | 192.168.60.11 | 60 | 1 | 2GB | Ubuntu 24 | BIND9 slave, ISC-DHCP secondary, chrony NTP |
| vm-web01 | 192.168.10.11 | 10,30 | 2 | 2GB | Ubuntu 24 | HAProxy :80, Apache :8080, WordPress |
| vm-web02 | 192.168.10.12 | 10,30 | 2 | 2GB | Ubuntu 24 | Apache :8080, WordPress replica |
| vm-services01 | 192.168.30.11 | 30 | 2 | 4GB | Ubuntu 24 | Postfix SMTP, Dovecot IMAP/POP3, Roundcube webmail, Dolibarr ERP, MySQL |
| vm-storage01 | 192.168.40.11 | 30,40 | 1 | 2GB | Ubuntu 24 | Samba AD join, NFS exports |
| vm-voip01 | 192.168.50.11 | 50 | 1 | 2GB | Ubuntu 24 | Asterisk 20.6, 3 extensiones SIP |
| vm-monitor01 | 192.168.70.11 | 70 | 2 | 4GB | Ubuntu 24 | Zabbix Server, Grafana nativa |
| vm-docker01 | 192.168.30.12 | 30 | 2 | 4GB | Ubuntu 24 | Docker, Grafana contenedor, Portainer CE |
| core1 | 192.168.1.10 | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP root |
| core2 | 192.168.1.11 | trunk | 2 | 4GB | Ubuntu 24 | FRR OSPF, Keepalived STP backup |
| pfSense | 192.168.10.1 | WAN | 2 | 2GB | pfSense | Firewall, NAT, CARP HA, VIPs, rutas estaticas |

## 4b. ISPs Remotos

| VM | WAN IP | WAN GW | LAN IP | Rol | Ubicacion |
|----|--------|--------|--------|-----|-----------|
| isp-aqp01 | 192.167.1.2/24 | 192.167.1.254 | 192.167.82.1/24 | Gateway NAT + Routing | Arequipa |
| isp-tru01 | 192.168.2.2/24 | 192.168.2.254 | 192.169.92.1/24 | Gateway NAT + Routing | Trujillo |

## 4c. VMs Arequipa

| VM | IP | VLAN | Servicios |
|----|-----|------|-----------|
| core-aqp | 192.167.82.2 | trunk | FRR OSPF, STP |
| aqp-dc01 | 192.167.82.62 | 60 | AD DNS local, DHCP local |
| aqp-dns01 | 192.167.82.63 | 60 | BIND9 slave local |
| aqp-voip01 | 192.167.82.64 | 50 | Asterisk local |

## 4d. VMs Trujillo

| VM | IP | VLAN | Servicios |
|----|-----|------|-----------|
| core-tru | 192.169.92.2 | trunk | FRR OSPF, STP |
| tru-dc01 | 192.169.92.62 | 60 | AD DNS local, DHCP local |
| tru-dns01 | 192.169.92.63 | 60 | BIND9 slave local |
| tru-voip01 | 192.169.92.64 | 50 | Asterisk local |

## 5. Active Directory

- **Dominio**: AXIOM.LOCAL (realm), AXIOM (NetBIOS)
- **DC**: vm-dc01 (192.168.16.10)
- **Admin password**: admin123!

### Usuarios AD

| Usuario | Grupo | Password |
|---------|-------|----------|
| jefazo | axiom-administradores | rol.123 |
| secretaria | axiom-secretaria | rol.123 |
| contador | axiom-usuarios | rol.123 |

### Grupos AD

| Grupo (winbind) | GID range | Proposito |
|------------------|-----------|-----------|
| axiom-administradores | 10000-20000 | Administradores |
| axiom-secretaria | 10000-20000 | Secretaria |
| axiom-usuarios | 10000-20000 | Usuarios generales |

### idmap config

- `*` : range 2000-9999
- `AXIOM` : range 10000-20000

## 6. DNS — BIND9 Failover

| Rol | VM | IP | Zonas |
|-----|-----|-----|-------|
| MASTER | vm-dc01 | 192.168.16.10 | AXIOM.local + reversas |
| SLAVE | vm-dns02 | 192.168.16.11 | Transferencia automatica via AXFR |

### Registros DNS (AXIOM.local)

| Registro | Tipo | Valor |
|----------|------|-------|
| vm-dc01 | A | 192.168.16.10 |
| dns02 | A | 192.168.16.11 |
| pfsense | A | 192.168.16.1 |
| vm-web01 | A | 192.168.11.11 |
| vm-web02 | A | 192.168.11.12 |
| mail | A | 192.168.13.11 |
| webmail | CNAME | mail |
| smtp | CNAME | mail |
| imap | CNAME | mail |
| storage | A | 192.168.14.11 |
| archivos | CNAME | storage |
| vm-docker01 | A | 192.168.13.12 |
| grafana | A | 192.168.13.12 |
| portainer | A | 192.168.13.12 |
| monitor | A | 192.168.17.11 |
| www | CNAME | vm-web01 |
| blog | A | 192.168.11.11 |
| _ldap._tcp | SRV | 0 100 389 vm-dc01 |
| _kerberos._tcp | SRV | 0 100 88 vm-dc01 |
| _kerberos._udp | SRV | 0 100 88 vm-dc01 |

## 7. DHCP — ISC Failover

| Rol | VM | IP | Puerto failover |
|-----|-----|-----|-----------------|
| PRIMARY | vm-dc01 | 192.168.16.10 | 647 |
| SECONDARY | vm-dns02 | 192.168.16.11 | 647 |

### Rangos DHCP

| VLAN | Subnet | Rango | Gateway |
|------|--------|-------|---------|
| 20 | 192.168.12.0/24 | .81 - .200 | 192.168.12.1 |
| 21 | 192.168.21.0/27 | .10 - .30 | 192.168.21.1 |
| 60 | 192.168.16.0/27 | .11 - .30 | 192.168.16.1 |

- Split: 128 (balanceo 50/50)
- MCLT: 3600s

## 8. NTP — chrony

- **Servidor**: vm-dns02 (192.168.16.11)
- **Permite**: 192.168.0.0/16
- **Upstream**: ntp.ubuntu.com, south-america.pool.ntp.org
- **Stratum local**: 10

## 9. Web — WordPress + HAProxy

### HAProxy (vm-web01 :80)

| Ruta | Backend | Detalle |
|------|---------|---------|
| `/` | vm-web01 :8080 + vm-web02 :8080 | roundrobin — WordPress |
| `/wp-*` | vm-web01 :8080 + vm-web02 :8080 | roundrobin |
| `/dolibarr/` | vm-services01 :80 | strip /dolibarr prefix |
| `/webmail` | vm-services01 :80 | — |
| `/voip` | vm-voip01 :80 | — |
| :8404/haproxy | Stats UI | admin / proxy.123 |

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

## 10. Email — Postfix + Dovecot + Roundcube

| Servicio | Puerto | Detalle |
|----------|--------|---------|
| SMTP | 25 | Postfix |
| IMAP | 993 | Dovecot (SSL) |
| POP3 | 995 | Dovecot (SSL) |
| Webmail | 80 /webmail/ | Roundcube |
| Auth | — | Winbind AD (secretaria / rol.123) |

- **MySQL root**: AdminMail123!

## 11. ERP — Dolibarr

- **URL**: http://192.168.11.11/dolibarr/ (via HAProxy)
- **Real**: http://192.168.13.11/ (root del servidor)
- **DB**: MySQL en vm-services01

## 12. Storage — Samba + NFS

### Samba Shares (vm-storage01)

| Share | Path | Permisos | Acceso |
|-------|------|----------|--------|
| Secretaria | /shared/departments/secretaria | axiom-secretaria | \\storage.AXIOM.local\Secretaria |
| Publico | /shared/public | todos | \\storage.AXIOM.local\Publico |

### NFS Exports

| Path | Clientes | Opciones |
|------|----------|----------|
| /shared/public | 192.168.20.0/24, 192.168.30.0/24 | rw,sync,no_subtree_check |
| /shared/departments | 192.168.20.0/24, 192.168.30.0/24 | rw,sync,no_subtree_check |
| /shared/projects | 192.168.20.0/24, 192.168.30.0/24 | rw,sync,no_subtree_check |

## 13. VoIP — Asterisk

- **Extensiones**: 100, 101, 102 (password: rol.123)
- **Protocolo**: SIP
- **Salida PSTN**: No configurada (falta gateway FXO/SIP)

## 14. Monitoreo — Zabbix + Grafana

### Zabbix Server (vm-monitor01)

- **URL**: http://axiom.monitor.AXIOM.local/zabbix/
- **Admin**: Admin / zabbix
- **Agentes monitoreados**:
  - vm-dc01 (192.168.60.10)
  - vm-dns02 (192.168.60.11)
  - vm-web01 (192.168.10.11)
  - vm-web02 (192.168.10.12)
  - vm-services01 (192.168.30.11)
  - vm-storage01 (192.168.40.11)
  - vm-voip01 (192.168.50.11)
  - vm-docker01 (192.168.30.12)
  - vm-monitor01 (192.168.70.11)
- **Auto-recovery**: vm-web01 se enciende automaticamente si nodata detectado

### Grafana Docker (vm-docker01)

- **Acceso directo**: http://axiom.grafana.AXIOM.local:3000
- **IP directa**: http://192.168.13.12:3000
- **Admin**: admin / grafana.123
- **Datasource Zabbix**: Configurar manualmente en UI (API: http://192.168.17.11/zabbix/api_jsonrpc.php, user: Admin, pass: zabbix)
- **Version**: 13.1.0

## 15. Docker — Portainer (vm-docker01)

- **Acceso directo HTTP**: http://axiom.portainer.AXIOM.local:9000
- **Acceso directo HTTPS**: https://axiom.portainer.AXIOM.local:9443
- **IP directa HTTP**: http://192.168.13.12:9000
- **IP directa HTTPS**: https://192.168.13.12:9443 (crear password al primer login)
- **Docker network**: axiom-net
- **Contenedores**: grafana, portainer

## 16. VPN — Tailscale

- **Nodo**: vm-vpn01 (cualquier VM con Tailscale)
- **Rutas anunciadas**: 192.168.0.0/16, 172.17.25.0/24
  - Lima: 192.168.0.0/16 completo
  - Arequipa: 192.167.82.0/24, 192.167.1.0/24
  - Trujillo: 192.169.92.0/24, 192.168.2.0/24
- **Acceso remoto**: Todas las subredes via Tailscale
- **Consumo de servicios centralizados**:
  - DNS Lima: 192.168.60.10, 192.168.60.11
  - AD Lima: 192.168.60.10
  - Zabbix Lima: 192.168.70.11
  - Web/Email/ERP Lima: 192.168.10.11

## 17. Networking — Cores Lima

### OSPF

- **Area**: 0.0.0.0
- **Core1 Router ID**: 10.0.0.1 (root bridge STP)
- **Core2 Router ID**: 10.0.0.2 (backup root STP)
- **Software**: FRR
- **Redes anunciadas**: 192.168.0.0/16

### Keepalived

- **Auth pass**: AN3IBL3P4SS
- **Interlink**: 10.0.0.0/30 (core1=10.0.0.1, core2=10.0.0.2)
- **Bond0**: ens34+ens35 (LAN hacia pfSenses)
- **Bond1**: ens36+ens37 (Trunks hacia pfSenses)

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
- **Uplink**: 192.169.92.1 (ISP-tru LAN gateway)
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
| Asterisk PBX (Tru) | http://192.169.92.64/ | extensiones 100/101/102 / rol.123 |

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
