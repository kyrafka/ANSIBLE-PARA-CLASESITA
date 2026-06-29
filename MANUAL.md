# MANUAL AXIOM TECH - Sistema Web + Email

## ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AXIOM TECH                                   │
│                                                                      │
│  ┌──────────────────┐         ┌──────────────────┐                 │
│  │   vm-web01       │         │  vm-services01   │                 │
│  │  (192.168.11.11) │         │ (192.168.13.11) │                 │
│  │                  │    DB   │                  │                 │
│  │  ┌──────────┐     │◄──────►│  ┌──────────┐    │                 │
│  │  │ WordPress│     │        │  │  MySQL   │    │                 │
│  │  │ (PHP)   │     │        │  │ axiom_web│    │                 │
│  │  └──────────┘     │        │  └──────────┘    │                 │
│  │       │           │        │       │          │                 │
│  │       ▼           │        │       ▼          │                 │
│  │  ┌──────────┐     │        │  ┌──────────┐    │                 │
│  │  │  Nginx   │     │        │  │  Postfix  │    │                 │
│  │  │  :80     │     │        │  │   :25    │    │                 │
│  │  └──────────┘     │        │  └──────────┘    │                 │
│  │       │           │        │       │          │                 │
│  │       │           │        │       ▼          │                 │
│  │       │           │        │  ┌──────────┐    │                 │
│  │       │           │        │  │  Dovecot  │    │                 │
│  │       │           │        │  │ :993 IMAP│    │                 │
│  │       │           │        │  │ :995 POP3│    │                 │
│  │       │           │        │  └──────────┘    │                 │
│  │       │           │        │       │          │                 │
│  │       │           │        │       ▼          │                 │
│  │       │           │        │  ┌──────────┐    │                 │
│  │       │           │        │  │ Roundcube│    │                 │
│  │       │           │        │  │  Webmail │    │                 │
│  │       │           │        │  │   :80    │    │                 │
│  │       │           │        │  └──────────┘    │                 │
│  └───────┼───────────┘        └───────┼───────────┘                 │
│          │                            │                             │
│          │                            │                             │
│          └────────────┬───────────────┘                             │
│                       │                                              │
│                       ▼                                              │
│                 ┌──────────┐                                         │
│                 │   DNS    │                                         │
│                 │  Server  │                                         │
│                 │vm-dc01   │                                         │
│                 │192.168.16.10│                                         │
│                 └──────────┘                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. SERVIDOR WEB (vm-web01)

### ¿Qué hace?
 Aloja el sitio web de AXIOM TECH con WordPress.

### Componentes:

| Componente | Función | Puerto |
|------------|---------|--------|
| **Nginx** | Servidor web (recibe peticiones HTTP) | 80 |
| **PHP 8.3-FPM** | Procesa código PHP de WordPress | - |
| **WordPress** | CMS para el blog y página corporativa | - |

### Archivos importantes:
- `/var/www/axiom/` - Directorio raíz del sitio web
- `/var/www/axiom/wp-config.php` - Configuración de WordPress
- `/var/www/axiom/index.html` - Página estática HTML (fallback)
- `/etc/nginx/sites-available/axiom` - Configuración Nginx

### URLs de acceso:
- **Sitio web**: http://192.168.11.11
- **WordPress Admin**: http://192.168.11.11/wp-admin
- **Usuario**: admin
- **Password**: 123

### ¿Cómo funciona?

1. Usuario escribe `http://192.168.11.11` en el navegador
2. Navegador envía petición a Nginx (puerto 80)
3. Nginx recibe la petición
4. Si es página PHP (WordPress), Nginx pasa a PHP-FPM
5. PHP-FPM procesa el código PHP
6. PHP conecta a MySQL (en vm-services01) para obtener contenido
7. PHP genera HTML y lo devuelve a Nginx
8. Nginx devuelve HTML al navegador

---

## 2. SERVIDOR DE EMAIL (vm-services01)

### ¿Qué hace?
 Gestiona el correo electrónico de la empresa.

### Componentes:

| Componente | Función | Puerto |
|------------|---------|--------|
| **MySQL** | Base de datos (usuarios, configuración) | 3306 |
| **Postfix** | Servidor SMTP (envío/recepción de emails) | 25 |
| **Dovecot** | Servidor IMAP/POP3 (acceso a correos) | 993, 995 |
| **Roundcube** | Webmail (leer emails desde el navegador) | 80 |

### Archivos importantes:
- `/var/lib/roundcube/` - Instalación de Roundcube
- `/var/www/html/webmail/` - Webmail accessible por navegador
- `/var/mail/[usuario]` - Buzones de email (formato Maildir)
- `/etc/postfix/main.cf` - Configuración de Postfix
- `/etc/dovecot/dovecot.conf` - Configuración de Dovecot

### URLs de acceso:
- **Webmail**: http://192.168.13.11/webmail/
- **Usuario**: mailuser
- **Password**: 123

### ¿Cómo funciona el correo?

#### Flujo de recepción de email:
```
Internet → Postfix (:25) → Dovecot → /var/mail/[usuario]
```

1. Un email llega desde Internet al puerto 25 (Postfix)
2. Postfix recibe el email
3. Postfix verifica el destinatario
4. Postfix guarda el email en `/var/mail/[usuario]` (formato Maildir)

#### Flujo de acceso via Webmail:
```
Navegador → Apache (:80) → Roundcube → Dovecot → /var/mail/[usuario]
```

1. Usuario accede a http://192.168.13.11/webmail/
2. Apache recibe la petición y pasa a Roundcube (PHP)
3. Roundcube pide al usuario credenciales
4. Roundcube verifica con Dovecot (IMAP)
5. Dovecot lee de `/var/mail/[usuario]`
6. Roundcube muestra los emails en el navegador

---

## 3. CONEXIÓN WEB ↔ EMAIL

### ¿Cómo interactúan?

```
┌────────────────┐         ┌────────────────┐
│    vm-web01    │         │ vm-services01  │
│                │         │                │
│  WordPress     │         │  MySQL         │
│    │          │         │    │           │
│    │          │         │    │           │
│    │    ───►  │         │    │           │
│    │   MySQL  │         │    │           │
│    │          │         │    │           │
│    │          │         │    │           │
│    │          │         │    │           │
│    ▼          │         │    ▼           │
│  Formulario    │         │  Postfix       │
│  Contacto      │         │  (SMTP)        │
└────────────────┘         └────────────────┘
```

### Formulario de contacto en WordPress:

1. Visitante llena formulario en la web (wp-content/plugins/contact-form-7)
2. WordPress conecta a MySQL (vm-services01) para guardar el mensaje
3. WordPress intenta enviar email via Postfix (en vm-services01)
4. Postfix recibe el email y lo entrega al buzón del usuario

### Base de datos MySQL:

| Tabla/Datos | Ubicación | Contenido |
|-------------|----------|-----------|
| `axiom_web` | vm-services01 | Contenido de WordPress (posts, usuarios, opciones) |
| `roundcube` | vm-services01 | Configuración de usuarios de Roundcube |
| `postfix` | vm-services01 | Base de datos de postfix |

---

## 4. FLUJO COMPLETO DE UN VISITANTE

### Visitante abre el sitio web:

```
1. Visitante escribe: http://192.168.11.11
2. DNS resuelve a 192.168.11.11
3. Navegador pide página a Nginx
4. Nginx → PHP-FPM → WordPress
5. WordPress → MySQL (vm-services01)
6. WordPress genera HTML
7. Navegador muestra página AXIOM TECH
```

### Visitante llena formulario de contacto:

```
1. Visitante llena formulario en http://192.168.11.11/contacto
2. WordPress procesa formulario
3. WordPress guarda mensaje en MySQL (axiom_web)
4. WordPress envia email via Postfix (vm-services01)
5. Postfix entrega email a buzón de admin
```

### Usuario revisa su correo via Webmail:

```
1. Usuario abre: http://192.168.13.11/webmail/
2. Apache → Roundcube (PHP)
3. Roundcube pide login
4. Dovecot verifica credenciales
5. Dovecot lee emails de /var/mail/mailuser
6. Roundcube muestra emails en navegador
```

---

## 5. USUARIOS Y CONTRASEÑAS

### Servidor Web (vm-web01):
| Servicio | Usuario | Password |
|---------|---------|----------|
| SSH | ubuntu | (tu key SSH) |
| WordPress | admin | 123 |
| MySQL (remoto) | axiom_web | Ax1omWeb!2024 |

### Servidor Email (vm-services01):
| Servicio | Usuario | Password |
|---------|---------|----------|
| SSH | ubuntu | (tu key SSH) |
| MySQL | root | AdminMail123! |
| MySQL | axiom_web | Ax1omWeb!2024 |
| IMAP/SMTP | mailuser | 123 |
| Webmail | mailuser | 123 |

---

## 6. COMANDOS ÚTILES

### Ver estado de servicios web:
```bash
ssh ubuntu@192.168.11.11 "systemctl status nginx php8.3-fpm"
```

### Ver estado de servicios email:
```bash
ssh ubuntu@192.168.13.11 "systemctl status postfix dovecot mysql apache2"
```

### Ver logs de email:
```bash
ssh ubuntu@192.168.13.11 "tail -20 /var/log/dovecot.log"
```

### Probar conexión MySQL desde web:
```bash
ssh ubuntu@192.168.11.11 "mysql -h 192.168.13.11 -u axiom_web -p'Ax1omWeb!2024' -e 'SELECT 1'"
```

### Ver emails de un usuario:
```bash
ssh ubuntu@192.168.13.11 "ls -la /var/mail/mailuser/"
```

---

## 7. RESOLUCIÓN DE PROBLEMAS

### La web no carga:
1. Verificar Nginx: `systemctl status nginx`
2. Verificar PHP: `systemctl status php8.3-fpm`
3. Ver logs: `tail /var/log/nginx/error.log`

### No llegan emails:
1. Verificar Postfix: `systemctl status postfix`
2. Ver logs: `tail /var/log/mail.log`
3. Verificar MX records en DNS

### No funciona Webmail:
1. Verificar Apache: `systemctl status apache2`
2. Verificar Roundcube: `curl http://localhost/webmail/`
3. Ver logs: `tail /var/log/roundcube/errors.log`

### No funciona login en Webmail:
1. Verificar Dovecot: `systemctl status dovecot`
2. Verificar usuario: `id mailuser`
3. Test auth: `doveadm auth test mailuser 123`

---

## 8. DIAGRAMA DE RED

```
Puertos y servicios:

vm-web01 (192.168.11.11):
  - :80   → Nginx (HTTP)
  - :443  → Nginx (HTTPS) - si configurado
  - :3306 → MySQL client (conecta a vm-services01)

vm-services01 (192.168.13.11):
  - :25   → Postfix (SMTP)
  - :80   → Apache + Roundcube (Webmail)
  - :143  → Dovecot (IMAP)
  - :993  → Dovecot (IMAPS)
  - :995  → Dovecot (POP3)
  - :3306 → MySQL (escucha en 0.0.0.0)

vm-dc01 (192.168.16.10):
  - :53   → DNS server
```

---

## 9. RESUMEN RÁPIDO

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde está el sitio web? | vm-web01 (192.168.11.11) |
| ¿Dónde está el webmail? | vm-services01 (192.168.13.11/webmail/) |
| ¿Dónde está la base de datos? | vm-services01 (MySQL) |
| ¿Qué usa WordPress para guardar datos? | MySQL en vm-services01 |
| ¿El formulario de contacto envía emails? | Sí, via Postfix en vm-services01 |
| ¿Puedo acceder al email desde el celular? | Sí, con IMAP (993) o Webmail |

---

## 10. PRÓXIMOS PASOS (Opcional)

- Configurar SSL/HTTPS
- Configurar servidor DNS para MX records
- Configurar Firewall (UFW/iptables)
- Instalar certificados Let's Encrypt
- Configurar backup automático
- Monitorear con Zabbix

---

**¿Alguna pregunta sobre el sistema?**