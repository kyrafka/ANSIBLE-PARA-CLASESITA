# Manual de Implementacion de VMs por VLAN
# Proyecto: Infraestructura de Red HA - Universidad

---

## 1. Resumen del Diseno de Red

| VLAN | Nombre | Subnet | Proposito |
|------|--------|--------|-----------|
| 10 | DMZ | 192.168.11.0/27 | Servicios publicos (Web, FTP) |
| 20 | Usuarios | 192.168.12.0/25 | PCs de estudiantes y profesores |
| 21 | Admin | 192.168.21.0/27 | Acceso administrativo restringido |
| 30 | Virtualizacion | 192.168.13.0/25 | Infraestructura virtual y dev |
| 40 | Storage | 192.168.14.0/26 | Samba, NFS, backups |
| 50 | VoIP | 192.168.15.0/26 | Telefonia IP (futura implementacion) |
| 60 | Gestion | 192.168.16.0/27 | DHCP, DNS, AD, Gestion central |
| 70 | Monitoreo | 192.168.17.0/27 | Zabbix, logs centralizados |
| 999 | HA_Sync | 192.168.99.0/30 | Comunicacion HA entre pfSense |

---

## 2. Asignacion de VMs por VLAN

| VM | VLAN | Sistema Operativo | CPU | RAM | Disco | Funcion |
|-----|------|-------------------|-----|-----|-------|---------|
| vm-dc01 | 60 | Windows Server 2022 | 2 vCPU | 4 GB | 60 GB | AD + DNS + DHCP |
| vm-dns02 | 30 | Ubuntu 24.04 LTS | 1 vCPU | 2 GB | 20 GB | DNS Secundario (BIND9) |
| vm-samba | 40 | Ubuntu 24.04 LTS | 2 vCPU | 4 GB | 80 GB | Samba + NFS + Backups |
| vm-web | 10 | Ubuntu 24.04 LTS | 1 vCPU | 2 GB | 20 GB | Nginx + PHP + MariaDB |
| vm-zabbix | 70 | Ubuntu 24.04 LTS | 2 vCPU | 4 GB | 40 GB | Monitoreo (Zabbix) |
| vm-backup | 60 | Ubuntu 24.04 LTS | 2 vCPU | 2 GB | 100 GB | Backups centralizados |
| vm-test-voip | 50 | Ubuntu 24.04 LTS | 1 vCPU | 2 GB | 10 GB | Pruebas de VoIP |
| vm-dev | 30 | Ubuntu 24.04 LTS | 1 vCPU | 2 GB | 20 GB | Desarrollo y pruebas |

---

## 3. Especificaciones Tecnicas por VM

### 3.1 vm-dns02 (DNS Secundario)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Ubuntu 24.04 Server LTS |
| **CPU** | 1 vCPU |
| **RAM** | 2 GB |
| **Disco** | 20 GB (Thin Provisioning) |
| **NIC** | 1x e1000 (VLAN 30) |
| **IP** | 192.168.13.10/25 |
| **Gateway** | 192.168.13.1 |
| **DNS** | 192.168.16.4 (AD), 8.8.8.8 |

#### Paquetes requeridos:
```bash
sudo apt update && sudo apt install -y bind9 bind9utils bind9-doc
sudo apt install -y net-tools htop curl wget
```

#### Servicios:
- BIND9 (DNS Secundario)
- Transferencia de zonas desde vm-dc01

---

### 3.2 vm-samba (Servidor de Archivos)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Ubuntu 24.04 Server LTS |
| **CPU** | 2 vCPU |
| **RAM** | 4 GB |
| **Disco** | 80 GB (Thin Provisioning) - expandible |
| **NIC** | 1x e1000 (VLAN 40) |
| **IP** | 192.168.14.10/26 |
| **Gateway** | 192.168.14.1 |

#### Paquetes requeridos:
```bash
sudo apt update && sudo apt install -y samba smbclient cifs-utils
sudo apt install -y nfs-kernel-server nfs-common
sudo apt install -y net-tools htop curl wget
```

#### Servicios:
- Samba (compartir archivos por VLAN)
- NFS (acceso entre servidores)
- Backups automaticos con rsync

---

### 3.3 vm-web (Servidor Web)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Ubuntu 24.04 Server LTS |
| **CPU** | 1 vCPU |
| **RAM** | 2 GB |
| **Disco** | 20 GB (Thin Provisioning) |
| **NIC** | 1x e1000 (VLAN 10) |
| **IP** | 192.168.11.10/27 |
| **Gateway** | 192.168.11.1 |

#### Paquetes requeridos:
```bash
sudo apt update && sudo apt install -y nginx php8.3-fpm php8.3-mysql mariadb-server
sudo apt install -y net-tools htop curl wget
```

#### Servicios:
- Nginx (web server)
- PHP 8.3
- MariaDB

---

### 3.4 vm-zabbix (Monitoreo)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Ubuntu 24.04 Server LTS |
| **CPU** | 2 vCPU |
| **RAM** | 4 GB |
| **Disco** | 40 GB (Thin Provisioning) - expandible por historial |
| **NIC** | 1x e1000 (VLAN 70) |
| **IP** | 192.168.17.10/27 |
| **Gateway** | 192.168.17.1 |

#### Paquetes requeridos:
```bash
sudo apt update && sudo apt install -y zabbix-server-mysql zabbix-frontend-php zabbix-agent
sudo apt install -y apache2 php8.3 php8.3-mysql php8.3-gd php8.3-bcmath php8.3-mbstring
sudo apt install -y net-tools htop curl wget
```

#### Servicios:
- Zabbix Server (monitoreo central)
- Zabbix Agent (auto-monitoreo)
- Apache + PHP para frontend

---

### 3.5 vm-backup (Backups Centralizados)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Ubuntu 24.04 Server LTS |
| **CPU** | 2 vCPU |
| **RAM** | 2 GB |
| **Disco** | 100 GB (Thick Provisioning) |
| **NIC** | 1x e1000 (VLAN 60) |
| **IP** | 192.168.16.10/27 |
| **Gateway** | 192.168.16.1 |

#### Paquetes requeridos:
```bash
sudo apt update && sudo apt install -y rsync rdiff-backup restic cron
sudo apt install -y net-tools htop curl wget
```

#### Servicios:
- Rsync (sincronizacion automatica)
- Restic (backups incrementales)
- Cron (automatizacion)

---

### 3.6 vm-dc01 (Active Directory)

| Campo | Especificacion |
|-------|----------------|
| **OS** | Windows Server 2022 |
| **CPU** | 2 vCPU |
| **RAM** | 4 GB |
| **Disco** | 60 GB (Thick Provisioning) |
| **NIC** | 1x e1000e (VLAN 60) |
| **IP** | 192.168.16.4/27 |
| **Gateway** | 192.168.16.1 |

#### Roles instalados:
- Active Directory Domain Services (AD DS)
- DNS Server
- DHCP Server
- Group Policy

---

## 4. Checklist de Configuracion

### 4.1 Configuracion Basica (TODAS las VMs)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar hostname
sudo hostnamectl set-hostname <nombre-vm>

# Instalar herramientas basicas
sudo apt install -y net-tools htop curl wget vim neofetch

# Configurar zona horaria
sudo timedatectl set-timezone America/Lima

# Desactivar IPv6 (opcional)
echo 'net.ipv6.conf.all.disable_ipv6 = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 4.2 Configuracion de Red (Ejemplo para VLAN 30)

```bash
# Configurar IP estatica en Netplan
sudo cat <<EOF > /etc/netplan/00-installer-config.yaml
network:
  version: 2
  ethernets:
    ens160:
      dhcp4: no
      addresses:
        - 192.168.13.10/25
      routes:
        - to: default
          via: 192.168.13.1
      nameservers:
        addresses:
          - 192.168.16.4
          - 8.8.8.8
EOF

sudo netplan apply
```

### 4.3 Firewall Basico (UFW)

```bash
# Instalar UFW
sudo apt install -y ufw

# Habilitar solo puertos necesarios
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (desde VLAN Admin)
sudo ufw allow from 192.168.21.0/27 to any port 22

# Habilitar
sudo ufw enable
```

---

## 5. Instrucciones por VM

### 5.1 Crear VM en ESXi

1. **Login** al vSphere Client
2. **Crear nueva VM** (`Create/Register VM`)
3. **Configuracion:**
   - **Name:** `vm-dns02`
   - **Compatibility:** ESXi 7.0 U3 o superior
   - **Guest OS:** Linux - Ubuntu Linux (64-bit)
   - **CPU:** 1 vCPU
   - **RAM:** 2 GB
   - **Disk:** 20 GB (Thin Provisioning)
   - **Network:** Port Group correspondiente a la VLAN
4. **Montar ISO:** Ubuntu 24.04 LTS Server
5. **Iniciar VM y completar instalacion**

### 5.2 Configuracion Post-Instalacion

```bash
# Login con credenciales creadas durante instalacion

# Actualizar
cd ~
sudo apt update && sudo apt upgrade -y

# Instalar cloud-init (si no esta)
sudo apt install -y cloud-init

# Reiniciar
sudo reboot
```

### 5.3 Conexion a Ansible (opcional)

```bash
# Instalar Python y dependencias para Ansible
sudo apt install -y python3 python3-pip python3-venv ssh

# Habilitar acceso SSH por clave
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

---

## 6. Mapa de Puertos y Servicios

| Puerto | Protocolo | Servicio | VM | VLAN |
|--------|-----------|----------|-----|------|
| 22 | TCP | SSH (acceso admin) | TODAS | 21 |
| 53 | UDP/TCP | DNS | vm-dc01, vm-dns02 | 60, 30 |
| 67/68 | UDP | DHCP | vm-dc01 | 60 |
| 80 | TCP | HTTP | vm-web | 10 |
| 443 | TCP | HTTPS | vm-web | 10 |
| 445 | TCP | SMB (Samba) | vm-samba | 40 |
| 10050 | TCP | Zabbix Agent | TODAS | 70 |
| 10051 | TCP | Zabbix Server | vm-zabbix | 70 |
| 3306 | TCP | MariaDB | vm-web | 10 |
| 111/2049 | TCP/UDP | NFS | vm-samba | 40 |
| 873 | TCP | Rsync | vm-backup | 60 |

---

## 7. Reglas de Firewall en pfSense

### 7.1 VLAN 10 (DMZ) → Internet
- Permitir HTTP (80) y HTTPS (443) SIN NAT (1:1 para IP publica)
- Denegar acceso a VLAN internas (20-70)

### 7.2 VLAN 20 (Usuarios) → Internet
- Permitir web generico (80, 443, 53, NTP)
- Denegar acceso a VLAN 21, 40, 60, 70

### 7.3 VLAN 21 (Admin) → TODAS
- Permitir todo hacia VLAN 10-70 (acceso admin)
- Solo desde IPs especificas (whitelist)

### 7.4 VLAN 40 (Storage) → VLAN 30, 60
- Permitir SMB (445) y NFS (2049) desde VLAN 30
- Permitir rsync (873) desde VLAN 60
- Denegar todo lo demas

---

## 8. Checklist Final de Verificacion

- [ ] Todas las VMs creadas en ESXi con especificaciones correctas
- [ ] IPs estaticas configuradas en todas las VMs
- [ ] Gateway apuntando a VIP (.1) de pfSense
- [ ] DNS apuntando a vm-dc01 (192.168.16.4)
- [ ] Zabbix Agent instalado y configurado en todas las VMs
- [ ] Firewall UFW activado con reglas minimas
- [ ] Backups automaticos configurados en vm-backup
- [ ] Samba compartiendo carpetas por VLAN en vm-samba
- [ ] DNS Secundario (BIND9) sincronizado con vm-dc01
- [ ] Web server accesible desde internet (port forwarding en pfSense)

---

## 9. Troubleshooting Comun

**No hay conectividad entre VMs:**
```bash
# Verificar VLAN en ESXi Port Group
# Verificar IP y mascara de subred
# Verificar gateway (debe ser .1)
# Verificar estado del bridge en los cores: ip -br a | grep br
```

**DNS no resuelve:**
```bash
# Verificar que /etc/resolv.conf apunte a 192.168.16.4
# Verificar que vm-dc01 esta encendido y en VLAN 60
# Verificar firewall en pfSense para puerto 53
```

**Zabbix no muestra metricas:**
```bash
# Verificar que Zabbix Agent esta corriendo
sudo systemctl status zabbix-agent

# Verificar configuracion del agente
sudo cat /etc/zabbix/zabbix_agentd.conf | grep Server=

# Verificar firewall (puerto 10050/10051)
```

---

**Documento version:** 1.0
**Fecha:** 2025-06-09
**Autor:** OpenCode + Diego
**Proyecto:** ANSIBLE-PARA-CLASESITA
