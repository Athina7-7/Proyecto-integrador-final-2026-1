# NGINX

`nginx.conf` configura a NGINX como proxy inverso y balanceador de carga.

## Puntos principales

- Puerto `80`: redirecciona a HTTPS.
- Puerto `443`: recibe HTTPS.
- `upstream backend_web`: contiene `web-en:5000` y `web-es:5000`.
- Politica de balanceo: round robin por defecto.
- `/admin/`: se envia a la aplicacion de estadisticas.
- `/`: se distribuye entre las dos aplicaciones web.

## Certificados

Para laboratorio, `scripts/deploy.sh` genera:

- `nginx/certs/fullchain.pem`
- `nginx/certs/privkey.pem`

Para AWS, reemplace esos archivos por los emitidos por Let's Encrypt para el dominio real. Nunca suba llaves privadas al repositorio.
