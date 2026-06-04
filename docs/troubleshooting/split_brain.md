# Troubleshooting: Split-Brain en Keepalived (VIPs duplicadas)

## ¿Qué es el Split-Brain?

Ocurre cuando **ambos Cores creen ser MASTER** y ambas IPs `.1` aparecen activas simultáneamente. Esto rompe la alta disponibilidad.

## Síntomas

```bash
# En Core 1 y Core 2 aparece algo como:
$ ip -br a | grep br10
br10    UP    192.168.11.4/27 192.168.11.1/27    # .1 DUPLICADA!
```

## Causas comunes

### 1. netplan apply limpia las VIPs de Keepalived
Cuando Ansible ejecuta `netplan apply` (via handler), Ubuntu re-levanta las interfaces estáticamente, ignorando momentáneamente las VIPs que Keepalived tiene asignadas.

**Solución:**
```bash
# Ejecutar en el BACKUP (Core 2):
sudo systemctl restart systemd-networkd
sudo systemctl restart keepalived
```

### 2. El interlink (br30) no transmite VRRP correctamente
Keepalived envía heartbeats por `unicast_src_ip` (br30: 192.168.13.x). Si el peer no recibe estos paquetes, no sabe quién es MASTER.

**Diagnóstico:**
```bash
# Ver logs de VRRP
grep -i 'vrrp\|keepalived' /var/log/syslog | tail -30

# Hacer ping por el bridge correcto (VLAN 30)
ping -I br30 192.168.13.4   # Desde Core 2
ping -I br30 192.168.13.5   # Desde Core 1
```

### 3. Prioridades mal configuradas
- Core 1 debe tener `priority 200`
- Core 2 debe tener `priority 100`

**Verificar:**
```bash
grep priority /etc/keepalived/keepalived.conf
```

### 4. Autenticación VRRP不一致
Ambos cores deben tener el mismo `auth_pass` en `/etc/keepalived/keepalived.conf`.

## Playbook de recuperación

```bash
# En el BACKUP (Core 2):
ansible-playbook playbooks/recover_vips.yml
```

## Tests para verificar split-brain

```bash
# Ejecutar en AMBOS cores:
ansible-playbook tests/keepalived/test_vrrp.yml -e "core_state=BACKUP"   # En Core 2
ansible-playbook tests/keepalived/test_vrrp.yml -e "core_state=MASTER"   # En Core 1

# Suite completa:
ansible-playbook tests/run_all.yml -e "core_id=core1"
```

## Checklist de troubleshooting

| Paso | Comando | Esperado |
|------|---------|----------|
| 1. Ver estado servicios | `sudo systemctl status keepalived frr` | Ambos ACTIVE |
| 2. Ver VIPs activas | `ip -br a \| grep br` | Solo .4 y .1 en MASTER |
| 3. Ver prioridades | `grep priority /etc/keepalived/keepalived.conf` | 200 y 100 |
| 4. Ping interlink | `ping -I br30 192.168.13.x` | Sin pérdida |
| 5. Vecino OSPF | `sudo vtysh -c 'show ip ospf neighbor'` | FULL |
| 6. Logs VRRP | `tail -20 /var/log/syslog \| grep -i vrrp` | Sin errores |

## Solución permanente

Si el problema persiste, agregar un segundo path de heartbeat en otra VLAN (por ejemplo, VLAN 20 además de VLAN 30) para que si un trunk falla, VRRP siga comunicándose por la otra VLAN.

## Referencias

- [Keepalived Documentation](http://www.keepalived.org/doc/)
- [VRRP Protocol](https://tools.ietf.org/html/rfc5798)