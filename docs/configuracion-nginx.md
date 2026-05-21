# Configuracion NGINX

## Rol

NGINX cumple dos funciones exigidas por el proyecto:

- Proxy inverso: recibe solicitudes del cliente y las reenvia a servicios internos.
- Balanceador de carga: reparte solicitudes entre Web Server 1 y Web Server 2.

## Upstream round robin

Archivo: `nginx/nginx.conf`

```nginx
upstream backend_web {
    server web-en:5000;
    server web-es:5000;
}
```

NGINX usa round robin por defecto cuando no se define otra politica. En modo multi-EC2, se reemplazan los nombres Docker por las IP privadas:

```nginx
upstream backend_web {
    server 10.0.2.11:5000;
    server 10.0.2.12:5000;
}
```

## HTTPS

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name _;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
}
```

En produccion, `server_name _;` debe reemplazarse por:

```nginx
server_name tudominio.com www.tudominio.com;
```

## Redireccion HTTP a HTTPS

```nginx
server {
    listen 80;
    server_name _;

    location / {
        return 301 https://$host$request_uri;
    }
}
```

## Encabezados reenviados

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
```

Estos encabezados permiten que Flask conozca el host original, la IP del cliente y el protocolo externo.

## Rutas

- `/`: round robin hacia `web-en` y `web-es`.
- `/admin/`: proxy hacia `stats`.
- `/nginx-health`: verificacion basica de NGINX.

## Validacion

```bash
docker compose exec nginx-lb nginx -t
curl -k https://www.dominio.com/nginx-health
```
