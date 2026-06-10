# Topologia Completa — 3 Sedes (Lima, Arequipa, Trujillo)
# Proyecto: tuempresa Peru S.A.C.

## 1. Sede Lima (Principal — HA Completo)

### WANs
| Link | ISP | IP Publica (ejemplo) |
|------|-----|------------------------|
| WAN1 | ISP Lima 1 | DHCP/Publica ISP |
| WAN2 | ISP Lima 2 | DHCP/Publica ISP |

### Redes LAN (VLANs Internas)
| VLAN | Nombre | Subnet | VIP (.1) | Core1 (.4) | Core2 (.5) |
|------|--------|--------|----------|------------|------------|
| 10 | DMZ | 192.168.11.0/27 | .1 | .4 | .5 |
| 20 | Usuarios | 192.168.12.0/25 | .1 | .4 | .5 |
| 21 | Admin | 192.168.21.0/27 | .1 | .4 | .5 |
| 30 | Virtualizacion | 192.168.13.0/25 | .1 | .4 | .5 |
| 40 | Storage | 192.168.14.0/26 | .1 | .4 | .5 |
| 50 | VoIP | 192.168.15.0/26 | .1 | .4 | .5 |
| 60 | Gestion | 192.168.16.0/27 | .1 | .4 | .5 |
| 70 | Monitoreo | 192.168.17.0/27 | .1 | .4 | .5 |
| 999 | HA_Sync | 192.168.99.0/30 | .254 | — | — |

### Interlink Cores
| Core | IP Interlink |
|------|-------------|
| Core1 (Lima) | 10.0.0.1/30 |
| Core2 (Lima) | 10.0.0.2/30 |

### OSPF Router IDs
| Equipo | Router ID |
|--------|-----------|
| Core1 Lima | 10.0.0.1 |
| Core2 Lima | 10.0.0.2 |

---

## 2. Sede Arequipa (Remota — Simplificada)

### WAN
| Link | ISP | Notas |
|------|-----|-------|
| WAN1 | ISP Arequipa | Con DHCP. No requiere doble WAN en sede remota (o si, para HA basica) |

### Redes LAN (Mismas VLANs, distinta subnet para no solapar)
| VLAN | Nombre | Subnet | Gateway | Router ID |
|------|--------|--------|---------|-----------|
| 10 | DMZ | 192.168.81.0/27 | .1 | — |
| 20 | Usuarios | 192.168.82.0/25 | .1 | — |
| 21 | Admin | 192.168.83.0/27 | .1 | — |
| 30 | Virtualizacion | 192.168.84.0/25 | .1 | — |
| 40 | Storage | 192.168.85.0/26 | .1 | — |
| 50 | VoIP | 192.168.86.0/26 | .1 | — |
| 60 | Gestion | 192.168.87.0/27 | .1 | — |
| 70 | Monitoreo | 192.168.88.0/27 | .1 | — |

### Equipo Arequipa (unico router/firewall)
| Rol | IP WAN | IP LAN |
|-----|--------|--------|
| Router/Firewall | DHCP ISP | 192.168.82.1/25 (VLAN 20) |

### VPN hacia Lima
- Tipo: IPsec Site-to-Site o OpenVPN
- Red remota (Lima): 192.168.0.0/16 (resumen)
- Red local (Arequipa): 192.168.82.0/25

---

## 3. Sede Trujillo (Remota — Simplificada)

### WAN
| Link | ISP | Notas |
|------|-----|-------|
| WAN1 | ISP Trujillo | Con DHCP |

### Redes LAN
| VLAN | Nombre | Subnet | Gateway |
|------|--------|--------|---------|
| 10 | DMZ | 192.168.91.0/27 | .1 |
| 20 | Usuarios | 192.168.92.0/25 | .1 |
| 21 | Admin | 192.168.93.0/27 | .1 |
| 30 | Virtualizacion | 192.168.94.0/25 | .1 |
| 40 | Storage | 192.168.95.0/26 | .1 |
| 50 | VoIP | 192.168.96.0/26 | .1 |
| 60 | Gestion | 192.168.97.0/27 | .1 |
| 70 | Monitoreo | 192.168.98.0/27 | .1 |

### VPN hacia Lima
- Misma configuracion que Arequipa pero con red 192.168.92.0/25

---

## 4. Resumen de Subnets por Sede

| Sede | Rango IP Principal | Prefix Identificador |
|------|--------------------|----------------------|
| Lima | 192.168.10-99.X | Original (ya definido) |
| Arequipa | 192.168.80-89.X | Tercer octeto +80 |
| Trujillo | 192.168.90-99.X | Tercer octeto +90 |

## 5. VPN Inter-Sedes (IPsec)

| Tuneles | Desde | Hacia | Red Local | Red Remota |
|---------|-------|-------|-----------|------------|
| 1 | Lima | Arequipa | 192.168.0.0/16 | 192.168.82.0/25 |
| 2 | Lima | Trujillo | 192.168.0.0/16 | 192.168.92.0/25 |
| 3 | Arequipa | Trujillo | 192.168.82.0/25 | 192.168.92.0/25 (opcional) |

## 6. DNS/Dominio Centralizado

| Servicio | Ubicacion | Notas |
|----------|-----------|-------|
| Active Directory | Lima (Samba DC) | Dominio: AJ.local |
| DNS Forwarder | Lima (Samba/BIND9) | 8.8.8.8 |
| DNS Sede Arequipa | Reenvio a Lima | Por VPN |
| DNS Sede Trujillo | Reenvio a Lima | Por VPN |

Las sedes Arequipa y Trujillo usan el DC de Lima via VPN para autenticacion.
