# Arquitectura Híbrida — tuempresa Perú S.A.C.

## Visión General

```
                        INTERNET
                            │
                            ▼
                    ┌───────────────┐
                    │  pfSense HA   │
                    │  (WAN CARP)   │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
       Core1 L2        Core2 L2       VLAN 10 DMZ
            │               │               │
            ▼               ▼               ▼
    ┌─────────────────────────────────────────┐
    │           VLAN 20 (Users)              │
    │      192.168.12.0/25                   │
    │                                         │
    │   vm-dc01 (AD/DNS/DHCP)                │
    │   vm-monitor01 (Zabbix)                │
    │   vm-storage01 (File Server)           │
    └──────────────────┬────────────────────┘
                       │
                       │  VPN Site-to-Site
                       │
                       ▼
    ┌─────────────────────────────────────────┐
    │              AWS VPC                    │
    │                                         │
    │  ┌─────────────┐  ┌─────────────────┐  │
    │  │ EC2         │  │ RDS MySQL       │  │
    │  │ Nginx       │  │ dolibarr_db     │  │
    │  │ HAProxy     │  └─────────────────┘  │
    │  │ Dolibarr    │                       │
    │  └─────────────┘                       │
    │         │                              │
    │  ┌─────────────┐                      │
    │  │ S3          │                      │
    │  │ backups     │                      │
    │  └─────────────┘                      │
    └─────────────────────────────────────────┘
```

---

## Servicios por Ubicación

### LOCAL — Lima (vm-dc01 como centro)

| VM | IP | Servicio | Puertos |
|----|----|----------|---------|
| vm-dc01 | 192.168.16.10 | AD, DNS, DHCP | 53, 389, 67 |
| vm-storage01 | 192.168.14.11 | File Server (NFS/Samba) | 445, 2049 |
| vm-monitor01 | 192.168.17.11 | Zabbix | 10051 |
| vm-web01 | 192.168.11.11 | HAProxy (redundancia local) | 80, 443 |

### AWS — Cloud

| Servicio | Detalle | Costo aprox |
|----------|---------|------------|
| EC2 t3.medium | Nginx + HAProxy + Dolibarr | $30-40/mes |
| RDS MySQL db.t3.micro | Base de datos ERP | $15-20/mes |
| S3 Standard | Backups | $5/mes |
| CloudWatch | Monitoreo AWS | Gratis |

---

## Direccionamiento IP

### Local (Lima)

| Red | Subnet | Uso |
|-----|--------|-----|
| VLAN 10 (DMZ) | 192.168.11.0/27 | Web público |
| VLAN 20 (Users) | 192.168.12.0/25 | Empleados |
| VLAN 30 (Services) | 192.168.13.0/25 | Servicios internos |
| VLAN 40 (Storage) | 192.168.14.0/26 | File server |
| VLAN 50 (VoIP) | 192.168.15.0/26 | Asterisk |
| VLAN 60 (Infra) | 192.168.16.0/27 | AD, DNS, DHCP, mgmt |
| VLAN 70 (Mon) | 192.168.17.0/27 | Zabbix |

### AWS VPC

| Red | Subnet | Uso |
|-----|--------|-----|
| VPC | 10.0.0.0/16 | Red AWS completa |
| Subnet pública | 10.0.1.0/24 | EC2 (conectado a internet) |
| Subnet privada | 10.0.2.0/24 | RDS (sin acceso internet) |
| Subnet vpn | 10.0.3.0/24 | Para túnel VPN |

---

## Conexión VPN Site-to-Site

```
pfSense (Lima) ◄═══════ VPN ════════► AWS VPC
192.168.16.1        OpenVPN         10.0.0.0/16
```

**Alternativas para la VPN:**
1. **OpenVPN** — installable en pfSense
2. **AWS Site-to-Site VPN** — crea túnel automático desde AWS
3. **WireGuard** — moderno y liviano

---

## Flujo de Tráfico

### Usuario accede al ERP (Dolibarr)

```
PC (VLAN 20: 192.168.12.x)
    │
    │ ¿Accede desde internet o red local?
    │
    ├─► INTERNET → pfSense → Core → [vm-web01 HAProxy] → ???

    └─► VPN → AWS EC2 (Dolibarr) → RDS MySQL
```

### Decisión de routing:

- **Desde internet** (fuera de la empresa):
  → Accede directo a AWS EC2 (sin pasar por local)

- **Desde VLAN 20** (usuarios internos):
  → VPN → AWS VPC → EC2 (más seguro, usa internet pero por túnel encriptado)

- **Acceso local sin VPN** (para demo):
  → HAProxy local reenvía directamente a AWS EC2 por internet

---

## Pasos de Implementación

### Fase 1: AWS (antes de la conexión)

1. Crear cuenta AWS (si no tienes)
2. Crear VPC con 3 subnets
3. Crear EC2 t3.medium con Nginx + HAProxy + Dolibarr
4. Crear RDS MySQL (privado)
5. Configurar Security Groups
6. Configurar Route 53 (DNS) o usar IP pública
7. Crear S3 bucket para backups

### Fase 2: Local

1. Mantener vm-dc01, vm-storage01, vm-monitor01
2. Configurar VPN en pfSense
3. Crear túnel VPN a AWS
4. Actualizar DNS local (vm-dc01) con registros hacia AWS

### Fase 3: Integración

1. Probar conectividad VPN
2. Configurar HAProxy local para failover a AWS
3. Configurar backups de vm-dc01 hacia S3
4. Monitorear desde Zabbix local + CloudWatch AWS

---

## Costos Estimados AWS (por mes)

| Servicio | Tipo | Costo |
|----------|------|-------|
| EC2 t3.medium | Linux | $30-40 |
| RDS MySQL | db.t3.micro | $15-20 |
| S3 | 50GB | $1-5 |
| Data Transfer | ~100GB | $10 |
| **TOTAL** | | **$56-75/mes** |

**Nota:** Con AWS Free Tier (12 meses) los costos son menores.

---

## DNS Records Necesarios

### En AWS Route 53 (o proveedor DNS)

| Registro | Tipo | Valor |
|----------|------|-------|
| erp.AJ.local | A | <EC2 Public IP> |
| web.AJ.local | A | <EC2 Public IP> |

### En vm-dc01 (Bind9 local)

| Registro | Tipo | Valor | Notas |
|----------|------|-------|-------|
| erp.AJ.local | CNAME | web.AJ.local | Redirige a AWS |
| web.AJ.local | A | <EC2 Public IP> | IP pública de AWS |
| files.AJ.local | A | 192.168.14.11 | File server local |
| monitor.AJ.local | A | 192.168.17.11 | Zabbix local |

---

## Backup Strategy (Regla 3-2-1)

| Tipo | Frecuencia | Local | S3 |
|------|------------|-------|-----|
| AD/LDAP | Diario | vm-dc01 | S3 |
| VMs | Semanal | ESXi | S3 |
| Files | Diario incremental | vm-storage01 | S3 |
| Configs | Cada cambio | vm-dc01 | S3 |

---

## Monitoreo Híbrido

| Qué | Cómo | Dónde |
|-----|------|-------|
| Hosts locales (cores, pfSense, VMs) | Zabbix Agent | vm-monitor01 |
| EC2 AWS | CloudWatch | AWS |
| RDS MySQL | CloudWatch | AWS |
| VPN estado | Zabbix + ping | vm-monitor01 |
| Aplicaciones | Health checks | Zabbix |

---

## Checklist de Implementación

- [ ] Crear AWS VPC
- [ ] Crear EC2 con Dolibarr
- [ ] Crear RDS MySQL
- [ ] Configurar Security Groups
- [ ] Configurar S3
- [ ] Crear VPN en pfSense
- [ ] Testear conectividad VPN
- [ ] Actualizar DNS local
- [ ] Configurar backups hacia S3
- [ ] Verificar acceso al ERP desde VLAN 20