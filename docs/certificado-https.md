# Certificado HTTPS

## Opcion recomendada: Let's Encrypt con Certbot

Requisitos:

- Dominio o subdominio publico apuntando al balanceador.
- Puerto `80` abierto temporalmente para validacion HTTP-01 o DNS configurable para validacion DNS-01.
- Puerto `443` abierto para HTTPS.
- Acceso SSH al balanceador.

Certbot recomienda tener un sitio HTTP disponible en el puerto `80` para varios metodos de validacion, o usar validacion DNS si no se puede abrir el puerto. Referencia oficial: https://certbot.eff.org/instructions?ws=nginx&os=linux

### Instalacion en Ubuntu

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/local/bin/certbot
```

### Generar certificado

Detener temporalmente NGINX si se usa `standalone`:

```bash
docker compose stop nginx-lb
sudo certbot certonly --standalone -d www.dominio.com -d dominio.com
```

Copiar certificados al directorio usado por Docker:

```bash
sudo cp /etc/letsencrypt/live/www.dominio.com/fullchain.pem nginx/certs/fullchain.pem
sudo cp /etc/letsencrypt/live/www.dominio.com/privkey.pem nginx/certs/privkey.pem
sudo chown "$USER":"$USER" nginx/certs/fullchain.pem nginx/certs/privkey.pem
docker compose up -d nginx-lb
```

### Renovacion

Probar renovacion:

```bash
sudo certbot renew --dry-run
```

Si se renueva el certificado, copiar los nuevos `.pem` y recargar NGINX:

```bash
sudo cp /etc/letsencrypt/live/www.dominio.com/fullchain.pem nginx/certs/fullchain.pem
sudo cp /etc/letsencrypt/live/www.dominio.com/privkey.pem nginx/certs/privkey.pem
docker compose exec nginx-lb nginx -s reload
```

## Opcion alternativa academica: certificado autofirmado

Solo para laboratorio:

```bash
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem \
  -subj "/CN=localhost"
```

Limitacion:

- El navegador mostrara advertencia porque no confia en la autoridad emisora.
- No se recomienda para la entrega final si el proyecto exige certificado de sitio valido.

## Evidencia requerida

Capturar:

- Navegador entrando a `https://www.dominio.com`.
- Candado o informacion del certificado.
- Salida de:

```bash
curl -Iv https://www.dominio.com
```
