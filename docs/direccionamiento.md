# Direccionamiento de red

## Criterio general

El cliente no pertenece a la red cloud. El cliente accede desde Internet usando la URL publica. En AWS se crea una VPC con subred publica para el balanceador y subred privada para aplicaciones y base de datos.

Este documento usa un direccionamiento de ejemplo coherente con AWS:

- VPC: `10.0.0.0/16`
- Subred publica: `10.0.1.0/24`
- Subred privada: `10.0.2.0/24`
- Mascara de cada subred `/24`: `255.255.255.0`
- Gateway logico de AWS: primera IP reservada por AWS en cada subred, representada como `.1`.

En AWS, las primeras cuatro IP y la ultima IP de cada subred estan reservadas. Por eso no se asignan direcciones como `10.0.1.0`, `10.0.1.1`, `10.0.1.2`, `10.0.1.3` ni `10.0.1.255`.

## Tabla de direccionamiento propuesta

| Componente | Tipo | IP privada | IP publica | Subred | Mascara | Gateway | Puertos permitidos | Justificacion |
|---|---|---:|---:|---|---|---:|---|---|
| Cliente externo | Cliente | No aplica a la VPC | IP dinamica del ISP | Internet | No aplica | Gateway del ISP | Salida TCP 443 y 80 | El cliente es una laptop/PC fuera de AWS. No se despliega en la nube. |
| NGINX Load Balancer | Balanceador | `10.0.1.10` | Elastic IP, ejemplo `54.x.x.x` | `10.0.1.0/24` publica | `255.255.255.0` | `10.0.1.1` | Entrada `80`, `443` desde Internet; `22` solo desde IP del equipo | Debe recibir trafico publico, terminar HTTPS y reenviar internamente. |
| Web Server 1 | Web | `10.0.2.11` | Ninguna | `10.0.2.0/24` privada | `255.255.255.0` | `10.0.2.1` | Entrada `5000` solo desde SG del balanceador | Aplicacion en ingles, no expuesta a Internet. |
| Web Server 2 | Web | `10.0.2.12` | Ninguna | `10.0.2.0/24` privada | `255.255.255.0` | `10.0.2.1` | Entrada `5000` solo desde SG del balanceador | Aplicacion en espanol, no expuesta a Internet. |
| Stats | Estadisticas | `10.0.2.30` | Ninguna | `10.0.2.0/24` privada | `255.255.255.0` | `10.0.2.1` | Entrada `5000` solo desde SG del balanceador; salida SMTP `587` o `465` | Panel interno publicado por NGINX en `/admin/stats`. |
| PostgreSQL | Base de datos | `10.0.2.20` | Ninguna | `10.0.2.0/24` privada | `255.255.255.0` | `10.0.2.1` | Entrada `5432` solo desde SG de web y stats | La base de datos solo acepta trafico interno. |

## Rutas

### Subred publica `10.0.1.0/24`

| Destino | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

Esta subred es publica porque su tabla de rutas tiene salida hacia un Internet Gateway. AWS documenta que una subred con ruta a un Internet Gateway se considera publica y una sin esa ruta se considera privada.

### Subred privada `10.0.2.0/24`

| Destino | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | NAT Gateway, opcional para actualizaciones |

Si el equipo no usa NAT Gateway por costo, puede instalar Docker en las instancias durante una ventana de configuracion controlada o usar el despliegue de laboratorio en una sola EC2. Lo importante para la sustentacion es no exponer Web 1, Web 2 ni PostgreSQL directamente a Internet.

## Security Groups propuestos

### `sg-lb`

Entrada:

- TCP `80` desde `0.0.0.0/0`.
- TCP `443` desde `0.0.0.0/0`.
- TCP `22` solo desde las IP publicas de los integrantes o desde VPN institucional.

Salida:

- TCP `5000` hacia `sg-web`.
- TCP `5000` hacia `sg-stats`.
- TCP `80/443` hacia Internet para Certbot/actualizaciones si aplica.

### `sg-web`

Entrada:

- TCP `5000` desde `sg-lb`.
- TCP `22` desde bastion, SSM o IP administrativa si la instancia es publica temporalmente.

Salida:

- TCP `5432` hacia `sg-db`.
- TCP `80/443` hacia NAT Gateway si requiere actualizaciones.

### `sg-stats`

Entrada:

- TCP `5000` desde `sg-lb`.

Salida:

- TCP `5432` hacia `sg-db`.
- TCP `587` o `465` hacia el servidor SMTP.

### `sg-db`

Entrada:

- TCP `5432` desde `sg-web`.
- TCP `5432` desde `sg-stats`.

Salida:

- Respuestas establecidas. Los Security Groups son stateful.

## Puertos Docker

| Servicio | Puerto contenedor | Puerto host | Exposicion |
|---|---:|---:|---|
| `nginx-lb` | `80`, `443` | `80`, `443` | Publica |
| `web-en` | `5000` | Ninguno | Solo red Docker interna |
| `web-es` | `5000` | Ninguno | Solo red Docker interna |
| `stats` | `5000` | Ninguno | Solo por NGINX |
| `db` | `5432` | Ninguno | Solo red Docker interna |

## Nota sobre mascaras

La VPC `10.0.0.0/16` permite hasta 65.536 direcciones teoricas antes de reservas. Las subredes `/24` se eligen para separar zonas publicas y privadas de forma simple. No se cambia la mascara para "dejar la misma subred"; cualquier cambio de mascara cambia el rango real de IPs, broadcast teorico y cantidad de direcciones. En AWS, el equipo debe documentar la VPC y subredes reales creadas en consola.
