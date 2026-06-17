# Firewall Rules — Lima (pfSense)

## Mapa de Interfaces

| Interface | Network | IP pfSense | VIP CARP | Notes |
|-----------|---------|------------|----------|-------|
| WAN1 | 192.168.2.0/30 | 192.168.2.2 | 192.168.2.100 | ISPCREATE1 (.1) |
| WAN2 | 192.168.1.0/30 | 192.168.1.2 | 192.168.1.200 | ISPCREATE2 (.1) |
| VLAN 10 (DMZ) | 192.168.11.0/27 | 192.168.11.1 | 192.168.11.1 | vm-web01 (.11) |
| VLAN 20 (Users) | 192.168.12.0/25 | 192.168.12.1 | 192.168.12.1 | DHCP relay → vm-dc01 |
| VLAN 60 (Infra) | 192.168.16.0/27 | 192.168.16.1 | 192.168.16.1 | vm-dc01 (.10), cores (.4/.5) |

## Reglas por Interface

---

### WAN1 (192.168.2.0/30) — ISPCREATE1

| # | Action | Protocol | Source | Dest | Port | Description |
|---|---|---|---|---|---|---|
| 1 | PASS | * | 192.168.2.1 | WAN1-addr | * | Gateway ISPCREATE1 |
| 2 | PASS | * | * | * | * | Salida internet (stateful) |
| 3 | BLOCK | * | * | * | * | Inbound bloqueado |

**Nota:** ISPCREATE1 tiene BGP AS65001, peer en 192.168.2.1.

---

### WAN2 (192.168.1.0/30) — ISPCREATE2

| # | Action | Protocol | Source | Dest | Port | Description |
|---|---|---|---|---|---|---|
| 1 | PASS | * | 192.168.1.1 | WAN2-addr | * | Gateway ISPCREATE2 |
| 2 | PASS | * | * | * | * | Salida internet (stateful) |
| 3 | BLOCK | * | * | * | * | Inbound bloqueado |

**Nota:** ISPCREATE2 tiene BGP AS65002, peer en 192.168.1.1.

---

### VLAN 60 — Infraestructura / AD / DNS / Gestión (192.168.16.0/27)

| # | Action | Protocol | Source | Dest | Port | Description |
|---|---|---|---|---|---|---|
| 1 | PASS | * | 192.168.12.0/25 | 192.168.16.0/27 | * | LAN → AD/DNS/DHCP |
| 2 | PASS | * | 192.168.13.0/25 | 192.168.16.0/27 | * | Servicios → DNS |
| 3 | PASS | TCP | 192.168.16.0/27 | * | 22 | SSH gestión (solo admins) |
| 4 | PASS | TCP | 192.168.16.0/27 | 192.168.11.11 | 8404 | HAProxy Stats (admins) |
| 5 | BLOCK | * | 192.168.11.0/27 | 192.168.16.0/27 | * | DMZ NO → Infraestructura |
| 6 | BLOCK | * | 192.168.1.0/30 | 192.168.16.0/27 | * | WAN2 NO → Infraestructura |
| 7 | BLOCK | * | 192.168.2.0/30 | 192.168.16.0/27 | * | WAN1 NO → Infraestructura |

**Servicios en esta VLAN:**
- vm-dc01: 192.168.16.10 (AD, DNS, DHCP)
- core1: 192.168.16.4
- core2: 192.168.16.5
- pfSense CARP VIP: 192.168.16.1

---

### VLAN 20 — Users / LAN (192.168.12.0/25)

| # | Action | Protocol | Source | Dest | Port | Description |
|---|---|---|---|---|---|---|
| 1 | PASS | * | 192.168.12.0/25 | * | * | Internet completo (NAT) |
| 2 | PASS | TCP | 192.168.12.0/25 | 192.168.16.10 | 53 | DNS vm-dc01 |
| 3 | PASS | * | 192.168.12.0/25 | 192.168.11.0/27 | * | Users → DMZ web |
| 4 | PASS | * | 192.168.12.0/25 | 192.168.13.0/25 | * | Users → Servicios |
| 5 | PASS | * | 192.168.12.0/25 | 192.168.15.0/26 | * | Users → VoIP |
| 6 | BLOCK | * | 192.168.12.0/25 | 192.168.14.0/26 | * | NO Storage directo |

**Notas:**
- DHCP relay configurado en pfSense → reenvía a vm-dc01 (192.168.16.10:67)
- Pool: 192.168.12.50-200
- Gateway: 192.168.12.1 (CARP VIP)

---

### VLAN 10 — DMZ / Web (192.168.11.0/27)

| # | Action | Protocol | Source | Dest | Port | Description |
|---|---|---|---|---|---|---|
| 1 | PASS | TCP | * | 192.168.11.11 | 80,443 | Web público desde WAN |
| 2 | PASS | TCP/UDP | 192.168.11.0/27 | 192.168.16.10 | 53 | DNS vm-dc01 |
| 3 | PASS | TCP | 192.168.11.0/27 | any | 80,443 | Actualizaciones salientes |
| 4 | BLOCK | * | 192.168.11.0/27 | 192.168.12.0/25 | * | DMZ NO → LAN Users |
| 5 | BLOCK | * | 192.168.11.0/27 | 192.168.16.0/27 | * | DMZ NO → Infraestructura |
| 6 | PASS | * | 192.168.12.0/25 | 192.168.11.0/27 | * | LAN → DMZ |
| 7 | BLOCK | ICMP | * | 192.168.11.11 | * | Sin ICMP desde WAN (seguridad) |

**Servicios en esta VLAN:**
- vm-web01: 192.168.11.11 (Nginx :8080 + HAProxy :80 + Stats :8404)
- HAProxy recibe tráfico WAN en :80/:443 y balancea a backend

---

## Notas de Configuración

### Order de reglas
pfSense evalúa reglas de arriba hacia abajo. Las reglas BLOCK deben estar **antes** de las PASS genéricas para que tengan efecto.

### Failover WAN
- WAN1 y WAN2 están en un **Gateway Group** para failover automático
- Si WAN1 cae, todo el tráfico sale por WAN2
- Las reglas PASS en WAN son stateless pero el seguimiento de estado (stateful) maneja las respuestas automáticamente

### NAT
- VLAN 20 → Internet: Outbound NAT automático (patrule) hacia ambas WANs
- DMZ (VLAN 10) → Internet: NAT Saliente por WAN (requiere NAT Outbound configurado)

### SSH Management
- Solo accesible desde VLAN 60 (192.168.16.0/27)
- Desactivar password auth, usar solo SSH keys
- Considerar cambiar puerto 22 a otro no estándar

### HAProxy Stats
- Listener: 192.168.11.11:8404/stats
- Accessible solo desde VLAN 60 (admins)
- Usuario/password: configurar en haproxy.cfg

---

## Checklist Post-Implementación

- [ ] Reglas aplicadas en pfSense Primary
- [ ] Reglas aplicadas en pfSense Backup (CARP sync)
- [ ] Test: PC en VLAN 20 tiene internet
- [ ] Test: PC en VLAN 20 resuelve `nslookup web.AJ.local`
- [ ] Test: Desde WAN (internet) puedo acceder a http://192.168.11.11
- [ ] Test: Desde VLAN 20 puedo ver HAProxy stats (si estoy en VLAN 60)
- [ ] Test: ICMP desde WAN a 192.168.11.11 bloqueado
- [ ] Test: Failover WAN (apagar WAN1, verificar que tráfico sale por WAN2)