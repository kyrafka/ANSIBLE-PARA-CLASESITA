# Manual: Configuración BGP en pfSense

## Topología

```
                    +----------------+
                    |   ISP_CREATE_WAN1  |  AS65001
     172.17.25.49   |  192.168.2.1   +----------+
     (WAN upstream)  +----------------+          |
                                                  | eBGP
                    +----------------+          |
                    |    pfSense1    | AS65000  |
     192.168.2.2 <--+                |  +------+
     (WAN1)         |                |  |
                    |  CARP VIP      |  | eBGP
     192.168.1.2 <--+  192.168.10.1  |  |
     (WAN2)         +----------------+  |
                                                  |
                    +----------------+          |
                    |   ISP_CREATE_WAN2  |  AS65002
     172.17.25.88   |  192.168.1.1   +----------+
     (WAN upstream)  +----------------+
```

## Pre-requisitos

1. **FRR instalado** en pfSense:
   - Menu: **System → Package Manager → Available Packages**
   - Instalar: **FRR**

2. **Interfaces WAN configuradas:**
   - WAN1 (opt1): `192.168.2.2/24` → gateway `192.168.2.1`
   - WAN2 (opt2): `192.168.1.2/24` → gateway `192.168.1.1`

---

## Configuración Paso a Paso

### Paso 1: Habilitar FRR

1. Ir a **Services → FRR**
2. **Enable FRR**: ✅
3. **Hostname**: `pfSense`
4. **Router ID**: `192.168.10.1` (VIP CARP)
5. **Log Level**: Informational
6. **Tick**: `Integrated_vtysh_config`
7. Click **Save**

### Paso 2: Configurar Zebra (Daemon básico)

Ir a **Services → FRR → Zebra**:

```conf
hostname pfSense
log syslog informational
!
interface wan1
  ip address 192.168.2.2/30
!
interface wan2
  ip address 192.168.1.2/30
!
ip forwarding
ipv6 forwarding
!
line vty
```

Click **Save**.

### Paso 3: Configurar BGP

Ir a **Services → FRR → BGP**:

```conf
router bgp 65000
  bgp router-id 192.168.10.1
  !
  !--- Peer WAN1 (ISPCREATE1, AS65001)
  neighbor 192.168.2.1 remote-as 65001
  neighbor 192.168.2.1 description ISPCREATE1-WAN1
  neighbor 192.168.2.1 timers 10 30
  neighbor 192.168.2.1 timers connect 10
  !
  !--- Peer WAN2 (ISPCREATE2, AS65002)
  neighbor 192.168.1.1 remote-as 65002
  neighbor 192.168.1.1 description ISPCREATE2-WAN2
  neighbor 192.168.1.1 timers 10 30
  neighbor 192.168.1.1 timers connect 10
  !
  !--- Redes a anunciar
  network 192.168.11.0/27    ! DMZ web
  network 192.168.12.0/25   ! LAN users
  network 192.168.15.0/26   ! VoIP
  !
  !--- Redistribuir rutas conectadas
  redistribute connected
  !
  !--- Acceso solo de peers
  access-list allow_peers permit 192.168.2.1/32
  access-list allow_peers permit 192.168.1.1/32
  access-list allow_peers deny any
  !
line vty
```

Click **Save**.

### Paso 4: Aplicar cambios

1. Ir a **Services → FRR**
2. Click **Apply Changes**
3. Esperar ~10 segundos

---

## Verificación

### Desde pfSense (vía SSH o Console):

```bash
# Ver estado BGP
vtysh -c 'show ip bgp summary'

# Ver vecinos
vtysh -c 'show ip bgp neighbors'

# Ver rutas aprendidas
vtysh -c 'show ip bgp'

# Rutas en tabla de enrutamiento
vtysh -c 'show ip route'
```

### Output esperado de `show ip bgp summary`:

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 192.168.10.1, local AS 65000 v3.0/3.0
Neighbor        AS    MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
192.168.2.1   65001       50      45       120    0    0 00:35:22            2
192.168.1.1   65002       48      43       120    0    0 00:35:20            2
Total number of neighbors 2
```

### Estado "State/PfxRcd" significa:
- **Numero > 0**: Neighbor UP, recibiendo prefijos
- **Idle**: Problema de conexión o AS incorrecto
- **Active**: Intentando conectar

---

## Troubleshooting

### Problema: Neighbor en Idle

1. **Verificar IP connectivity**:
   ```bash
   ping 192.168.2.1  # Desde pfSense
   ```

2. **Verificar que ISP tenga FRR corriendo**:
   ```bash
   # En ISP_CREATE_WAN1/WAN2
   vtysh -c 'show ip bgp summary'
   ```

3. **Verificar AS correto** en ambos lados

### Problema: No recibe rutas

1. **Verificar que ISPs estén anunciando**:
   ```bash
   # En ISP_CREATE1
   vtysh -c 'show ip bgp'
   ```

2. **Verificar networks en BGP config**:
   - En ISP: verificar que tenga `network 172.17.25.0/24` (WAN)
   - En pfSense: verificar que tenga las redes internas

### Problema: FRR no inicia

```bash
# Ver logs
tail -f /var/log/frr/frr.log

# Reiniciar
/usr/local/sbin/frr.init restart

# Ver estado
systemctl status frr
```

---

## Comandos útiles FRR/BGP

| Comando | Descripción |
|---------|-------------|
| `show ip bgp summary` | Resumen de vecinos BGP |
| `show ip bgp neighbors` | Detalle de cada vecino |
| `show ip bgp` | Todas las rutas BGP |
| `show ip bgp 192.168.11.0/27` | Info de ruta específica |
| `show ip route` | Tabla de enrutamiento completa |
| `clear ip bgp * soft` | Resetear conexiones |

---

## Redes anunciadas desde pfSense (AS65000)

| Red | Descripción | VLAN |
|-----|-------------|------|
| 192.168.11.0/27 | DMZ Web (webmail, erp) | 10 |
| 192.168.12.0/25 | LAN Users | 20 |
| 192.168.15.0/26 | VoIP | 50 |

## Redes anunciadas desde ISPs

| ISP | Red | Descripción |
|-----|-----|-------------|
| ISPCREATE1 (AS65001) | 172.17.25.0/24 | WAN upstream |
| ISPCREATE2 (AS65002) | 172.17.25.0/24 | WAN upstream |

---

## Firewall Rules necesarias en pfSense

Para permitir BGP (TCP 179) en cada WAN:

**WAN1 (opt1) - ISPCREATE1:**
- Action: Pass
- Interface: WAN1
- Protocol: TCP
- Source: 192.168.2.1/32
- Destination: WAN1 address
- Port: 179

**WAN2 (opt2) - ISPCREATE2:**
- Action: Pass
- Interface: WAN2
- Protocol: TCP
- Source: 192.168.1.1/32
- Destination: WAN2 address
- Port: 179

O más permisivo (solo desde IPs de ISPs):
- Protocol: TCP
- Source: 192.168.2.0/24, 192.168.1.0/24
- Destination: any
- Port: 179