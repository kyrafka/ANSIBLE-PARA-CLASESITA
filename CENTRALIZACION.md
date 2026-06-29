# CENTRALIZACIÓN DE DATOS - AXIOM TECH

## ARQUITECTURA CENTRALIZADA

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           AXIOM TECH - INFRAESTRUCTURA                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   vm-dc01 (192.168.16.10)                                                │
│   ══════════════════════                                                │
│   Active Directory + DNS                                               │
│   • Usuarios y grupos (Autenticación centralizada)                       │
│   • Politicas de dominio                                                 │
│   • DNS zones (axiom.local, axiom.tech)                                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
│   vm-web01      │    │   vm-services01       │    │   vm-monitor01  │
│  192.168.11.11 │    │   192.168.13.11        │    │   192.168.17.11  │
│ ════════════════│    │ ════════════════════════│    │ ════════════════│
│                 │    │                        │    │                 │
│  ┌───────────┐  │    │  ┌────────────────┐   │    │  ┌───────────┐  │
│  │  Nginx    │  │    │  │  Apache       │   │    │  │  Zabbix  │  │
│  │  :80      │  │    │  │  Roundcube     │   │    │  │  Server  │  │
│  └───────────┘  │    │  │  Dolibarr ERP  │   │    │  └───────────┘  │
│       │         │    │  └────────────────┘   │    │       │         │
│       ▼         │    │        │             │    │       ▼         │
│  ┌───────────┐  │    │        ▼             │    │  ┌───────────┐  │
│  │ WordPress │  │    │  ┌────────────────┐  │    │  │ MySQL     │  │
│  │  (PHP)    │──┼────┼──►│  MySQL         │  │    │  │  (Zabbix)│  │
│  │           │  │    │  │  axiom_web    │  │    │  └───────────┘  │
│  │           │  │    │  │  dolibarr      │  │    │       │         │
│  │           │  │    │  │  postfix       │  │    │       ▼         │
│  │           │  │    │  │  roundcube     │  │    │  ┌───────────┐  │
│  └───────────┘  │    │  └────────────────┘  │    │  │ Grafana  │  │
│       │         │    │        │             │    │  └───────────┘  │
│       │         │    │        ▼             │    │                 │
│       │         │    │  ┌────────────────┐   │    │                 │
│       │         │    │  │  Postfix      │   │    │                 │
│       │         │    │  │  SMTP :25     │   │    │                 │
│       │         │    │  └────────────────┘   │    │                 │
│       │         │    │        │             │    │                 │
│       │         │    │        ▼             │    │                 │
│       │         │    │  ┌────────────────┐  │    │                 │
│       │         │    │  │  Dovecot       │  │    │                 │
│       │         │    │  │  IMAP :993     │  │    │                 │
│       │         │    │  └────────────────┘  │    │                 │
│       │         │    │        │             │    │                 │
│       │         │    │        ▼             │    │                 │
│       │         │    │  ┌────────────────┐  │    │                 │
│       │         │    │  │  /var/mail/   │  │    │                 │
│       │         │    │  │  (emails)     │  │    │                 │
│       │         │    │  └────────────────┘  │    │                 │
└───────┼─────────┘    └──────────┬──────────┘    └─────────────────┘
        │                           │
        │         ┌─────────────────┼─────────────────┐
        │         │                 │                 │
        ▼         ▼                 ▼                 │
┌─────────────────────────────────────────────┐
│           vm-storage01 (192.168.14.11)       │
│           ════════════════════════════       │
│                                                │
│   ┌──────────────────────────────────────┐   │
│   │         SAMBA - Archivos              │   │
│   │  ┌────────────────────────────────┐   │   │
│   │  │  /srv/samba/                   │   │   │
│   │  │   ├── Jefatura/  (10-80)     │   │   │
│   │  │   ├── Secretaria/ (81-100)     │   │   │
│   │  │   ├── Usuarios/  (101-200)    │   │   │
│   │  │   └── Publico/   (solo lect) │   │   │
│   │  └────────────────────────────────┘   │   │
│   └──────────────────────────────────────┘   │
│                                                │
│   ┌──────────────────────────────────────┐   │
│   │         NFS - Backups                │   │
│   │  /srv/nfs/backups                   │   │
│   └──────────────────────────────────────┘   │
│                                                │
└─────────────────────────────────────────────┘
```

---

## BASE DE DATOS CENTRALIZADA (MySQL en vm-services01)

| Base de Datos | Para qué | Usuario | Acceso desde |
|---|---|---|---|
| **axiom_web** | WordPress (contenido web) | axiom_web / Ax1omWeb!2024 | vm-web01 ✓ |
| **dolibarr** | ERP Dolibarr | dolibarr_user / Dol1b4rr2024! | Local |
| **postfix** | Configuración email | root / AdminMail123! | Local |
| **roundcube** | Usuarios webmail | root / AdminMail123! | Local |

### Ubicación física:
```
vm-services01 (192.168.13.11)
└── /var/lib/mysql/
    ├── axiom_web/           (WordPress)
    ├── dolibarr/             (ERP)
    ├── postfix/              (Email config)
    └── roundcube/            (Webmail)
```

---

## ARCHIVOS CENTRALIZADOS (Samba en vm-storage01)

| Carpeta | Contenido | Grupo AD | IPs permitidas |
|---|---|---|---|
| **/srv/samba/Jefatura/** | Documentos directivos | AXIOM+Administradores | 192.168.12.10-80 |
| **/srv/samba/Secretaria/** | Actas, contratos | AXIOM+Secretaria | 192.168.12.81-100 |
| **/srv/samba/Usuarios/** | Archivos generales | AXIOM+Usuarios | 192.168.12.101-200 |
| **/srv/samba/Publico/** | Info pública | AXIOM+Domain Users | Solo lectura |
| **/srv/samba/homes/** | Carpeta personal por usuario | Su usuario | Solo el usuario |

### Ubicación física:
```
vm-storage01 (192.168.14.11)
└── /srv/samba/
    ├── Jefatura/              (subcarpetas: Proyectos, Finanzas, RH, Legal)
    ├── Secretaria/           (subcarpetas: Actas, Contratos, Correspondencia)
    ├── Usuarios/             (subcarpetas: General, Documentos, Templates)
    ├── Publico/
    └── homes/                (carpeta personal por usuario AD)
```

---

## SERVICIOS CENTRALIZADOS

### AUTENTICACIÓN (vm-dc01 - AD)
```
• Active Directory Domain Services
• DNS Server  
• DHCP Server
• Kerberos
• LDAP

Dominio: AXIOM.local
Base DN: DC=AXIOM,DC=LOCAL
```

### EMAIL (vm-services01)
```
• Postfix (SMTP - puerto 25)
• Dovecot (IMAP - puerto 993, POP3 - puerto 995)
• Roundcube (Webmail - puerto 80)
• SpamAssassin (antispam)

/var/mail/[usuario]  →  Buzones de email
```

### WEB (vm-web01)
```
• Nginx (puerto 80)
• PHP 8.3-FPM
• WordPress

/var/www/axiom/      →  Sitio web completo
```

### MONITOREO (vm-monitor01)
```
• Zabbix Server
• Grafana
• MySQL (base zabbix)

/var/lib/zabbix/     →  Datos de monitoreo
```

---

## RESUMEN: ¿DÓNDE ESTÁ TODO?

| Recurso | Ubicación | IP | Puerto |
|---|---|---|---|
| Sitio Web (WordPress) | vm-web01 | 192.168.11.11 | 80 |
| Blog Web | vm-web01 | 192.168.11.11 | 80 |
| Base de datos (WordPress) | vm-services01 | 192.168.13.11 | 3306 |
| Base de datos (Dolibarr) | vm-services01 | 192.168.13.11 | 3306 |
| Webmail (Roundcube) | vm-services01 | 192.168.13.11 | 80 |
| Email (IMAP) | vm-services01 | 192.168.13.11 | 993 |
| Email (SMTP) | vm-services01 | 192.168.13.11 | 25 |
| ERP (Dolibarr) | vm-services01 | 192.168.13.11 | 80 |
| Archivos compartidos (SMB) | vm-storage01 | 192.168.14.11 | 445 |
| Backups NFS | vm-storage01 | 192.168.14.11 | 2049 |
| Monitoreo (Zabbix) | vm-monitor01 | 192.168.17.11 | 80 |
| Active Directory | vm-dc01 | 192.168.16.10 | 389, 636 |
| DNS | vm-dc01 | 192.168.16.10 | 53 |

---

## FLUJOS DE DATOS

### Usuario accede a la web:
```
Usuario → vm-web01 (Nginx) → WordPress → MySQL (vm-services01)
```

### Usuario accede a archivos compartidos:
```
Usuario → vm-storage01 (Samba) → Verifica IP → Verifica AD → Entrega archivos
```

### Usuario accede a email via webmail:
```
Usuario → vm-services01 (Apache) → Roundcube → Dovecot → /var/mail
```

### Usuario verifica AD desde cualquier servicio:
```
Servicio → vm-dc01 (Kerberos/LDAP) → Autenticación
```

---

## BACKUPS

| Qué | Dónde | Cada cuánto |
|---|---|---|
| Base de datos MySQL | vm-storage01 (/srv/nfs/backups/) | Diario |
| Archivos web | vm-storage01 | Semanal |
| Emails | vm-storage01 | Diario |
| Configuraciones | vm-storage01 | Semanal |
| VMs completas | Proxmox Backup Server | Diario |

---

## ACCESO DESDE INTERNET (futuro)

```
                    INTERNET
                        │
                        ▼
                ┌───────────────┐
                │  pfSense/CORE │
                │  Firewall    │
                └───────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐   ┌─────────┐
   │  Web    │    │  Email   │   │  VPN   │
   │ :80/443 │    │  :25,993 │   │  :1194 │
   └─────────┘    └──────────┘   └─────────┘
```

---

**¿Alguna duda sobre la arquitectura? ¿Qué más querés agregar o ajustar?**