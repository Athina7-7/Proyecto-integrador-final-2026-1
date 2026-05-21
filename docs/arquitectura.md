# Arquitectura del proyecto

## Analisis de requisitos

### Objetivo general

Desplegar en AWS una aplicacion web segura, accesible desde Internet por una URL publica con HTTPS, que registre aspirantes interesados en estudiar una carrera, almacene la informacion en base de datos, balancee trafico entre dos servidores web y genere estadisticas con graficas enviadas por correo.

### Componentes obligatorios

- Cliente externo fuera de la nube: computador o laptop con navegador comercial.
- Dominio publico o subdominio publico.
- Registro DNS tipo A apuntando a la IP publica del balanceador.
- Certificado HTTPS valido para el dominio.
- Balanceador NGINX como proxy inverso con politica round robin.
- Dos servidores web en Docker.
- Base de datos en Docker.
- Aplicacion web en Python o C. Este repositorio usa Python Flask.
- Registro de nombre, comuna, fecha de ingreso y carrera de interes.
- Carreras: Medicina, Ingeniería, Abogacía y Licenciatura, con equivalentes en ingles para el servidor en ingles.
- Aplicacion o endpoint de estadisticas con graficas.
- Envio de estadisticas por correo a `ialondonoo@eafit.edu.co`.
- Despliegue final en Amazon AWS.

### Componentes opcionales o alternativos

- Certificado autofirmado solo para laboratorio, no recomendado para entrega final porque genera advertencia en el navegador.
- Aplicacion de estadisticas separada en un contenedor propio, como se implementa en este repositorio.
- NAT Gateway o bastion host para administrar instancias privadas. No es obligatorio para demostrar la aplicacion, pero mejora la operacion.
- Despliegue economico en una sola EC2 con varios contenedores para pruebas. Para sustentacion estricta, se recomienda separar balanceador, web 1, web 2 y base de datos en VMs distintas.

### Entregables operacionales

- URL publica con HTTPS, por ejemplo `https://www.dominio.com`.
- DNS resolviendo hacia la IP publica del balanceador.
- NGINX recibiendo HTTPS y reenviando a los servidores web.
- Balanceo round robin visible alternando entre Web Server 1 y Web Server 2.
- Formulario funcional de registro.
- Insercion de datos en PostgreSQL.
- Panel de estadisticas en `/admin/stats`.
- Envio SMTP del reporte a `ialondonoo@eafit.edu.co`.

### Entregables documentales

- Repositorio GitHub con codigo, Dockerfiles, Compose, configuracion NGINX, SQL, scripts y documentacion.
- Informe final en PDF con portada, integrantes, arquitectura, direccionamiento, configuraciones, pruebas, capturas, problemas, conclusiones, URL publica y anexos.
- Evidencias: capturas de AWS, DNS, HTTPS, balanceo, base de datos, graficas y correo enviado.

### Restricciones tecnicas

- El cliente no esta en AWS. El cliente es el computador externo que accede por Internet.
- Solo el balanceador debe tener IP publica para HTTP/HTTPS.
- Los servidores web y la base de datos no deben exponerse directamente a Internet.
- La base de datos solo debe aceptar conexiones internas desde las aplicaciones.
- No se deben cambiar mascaras de red sin justificacion. El direccionamiento debe corresponder a la VPC/subred real de AWS.
- Docker es obligatorio.
- El balanceador debe ser NGINX como proxy inverso con round robin.

### Fecha y forma de entrega

El enunciado recibido no incluye una fecha exacta. La forma de entrega indicada es un informe final en PDF por EAFIT Interactiva, con nombre formado por el primer apellido de los integrantes, mas el repositorio GitHub y la URL publica del sitio.

### Elementos a demostrar en sustentacion

- Acceso desde un navegador externo a la URL HTTPS.
- Resolucion DNS del dominio al balanceador.
- Certificado del sitio.
- Alternancia de servidores al hacer varias solicitudes.
- Registro exitoso desde ambos servidores web.
- Datos persistidos en PostgreSQL.
- Estadisticas por comuna y por comuna/carrera.
- Envio de correo al destinatario exigido.
- Explicacion del direccionamiento IP, subredes, puertos y reglas de seguridad.

## Arquitectura logica

```text
Cliente externo
     |
     | HTTPS 443 / HTTP 80
     v
DNS publico: www.dominio.com -> IP publica del balanceador
     |
     v
EC2 Balanceador publico
  Docker: nginx-lb
  - Termina HTTPS
  - Proxy inverso
  - Round robin
     |
     | HTTP interno 5000
     +-------------------------+
     |                         |
     v                         v
EC2 Web Server 1          EC2 Web Server 2
Docker: web-en            Docker: web-es
Flask ingles              Flask espanol
     |                         |
     +-----------+-------------+
                 |
                 | PostgreSQL 5432 interno
                 v
          EC2 Base de datos
          Docker: db
          PostgreSQL
                 ^
                 |
          EC2/Contenedor stats
          Docker: stats
          Graficas + SMTP
```

## Diagrama Mermaid

```mermaid
flowchart LR
    C[Cliente externo<br/>PC o laptop fuera de AWS] -->|https://www.dominio.com:443| DNS[DNS publico<br/>Registro A]
    DNS -->|IP publica| LB[EC2 publica<br/>Docker: nginx-lb<br/>NGINX HTTPS + reverse proxy]
    LB -->|Round robin HTTP 5000| WEN[EC2 privada<br/>Docker: web-en<br/>Web Server 1 - English]
    LB -->|Round robin HTTP 5000| WES[EC2 privada<br/>Docker: web-es<br/>Web Server 2 - Espanol]
    LB -->|/admin/stats HTTP 5000| STATS[EC2 privada o contenedor<br/>Docker: stats]
    WEN -->|PostgreSQL 5432| DB[(EC2 privada<br/>Docker: PostgreSQL)]
    WES -->|PostgreSQL 5432| DB
    STATS -->|Consulta 5432| DB
    STATS -->|SMTP 587/465| MAIL[Servidor SMTP externo]
    MAIL -->|Reporte| PROF[ialondonoo@eafit.edu.co]
```

## Flujo de solicitud

1. El usuario abre `https://www.dominio.com` desde su computador externo.
2. DNS resuelve `www.dominio.com` hacia la IP publica del balanceador.
3. NGINX recibe la conexion HTTPS en el puerto `443`.
4. NGINX valida el certificado y actua como proxy inverso.
5. NGINX reparte las solicitudes entre `web-en` y `web-es` con round robin.
6. El servidor web que recibe la solicitud procesa el formulario.
7. La aplicacion guarda nombre, comuna, fecha de ingreso, carrera, idioma y servidor en PostgreSQL.
8. El administrador entra a `/admin/stats`.
9. La aplicacion de estadisticas consulta la base de datos, genera graficas y permite enviar el reporte por correo.

## Modos de despliegue

### Modo laboratorio o presupuesto bajo

Una sola EC2 publica ejecuta `docker compose up -d --build` y levanta todos los contenedores. Es util para pruebas, desarrollo y demostracion inicial. Solo se expone `80` y `443`; PostgreSQL y Flask quedan sin puertos publicados al host.

### Modo AWS recomendado para sustentacion estricta

Se usan instancias separadas:

- EC2 publica para `nginx-lb`.
- EC2 privada para `web-en`.
- EC2 privada para `web-es`.
- EC2 privada para `db`.
- EC2 privada o contenedor interno para `stats`.

En este modo, `nginx/nginx.conf` debe cambiar:

```nginx
upstream backend_web {
    server 10.0.2.11:5000;
    server 10.0.2.12:5000;
}

upstream stats_app {
    server 10.0.2.30:5000;
}
```

Las IPs anteriores son ejemplo y deben reemplazarse por las IP privadas reales de AWS.
