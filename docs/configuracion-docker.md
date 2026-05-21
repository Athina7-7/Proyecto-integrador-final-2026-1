# Configuracion Docker

## Servicios definidos

`docker-compose.yml` levanta:

- `nginx-lb`: balanceador NGINX.
- `web-en`: Web Server 1 en ingles.
- `web-es`: Web Server 2 en espanol.
- `db`: PostgreSQL.
- `stats`: estadisticas y correo.

## Redes Docker

- `public`: conecta el balanceador con el host para publicar `80` y `443`.
- `backend`: conecta NGINX, Flask, stats y PostgreSQL internamente.

Los servicios web y base de datos usan `expose`, no `ports`, por lo tanto no quedan publicados directamente en el host.

## Variables de entorno

Copiar:

```bash
cp .env.example .env
```

Editar:

```env
DOMAIN_NAME=www.dominio.com
PUBLIC_URL=https://www.dominio.com
DB_NAME=telematica
DB_USER=telematica_user
DB_PASSWORD=<password_seguro>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<correo>
SMTP_PASSWORD=<app_password>
SMTP_FROM=<correo>
SMTP_TO=ialondonoo@eafit.edu.co
ADMIN_TOKEN=<token_largo>
```

## Levantar servicios

```bash
./scripts/deploy.sh
```

O manualmente:

```bash
docker compose up -d --build
```

## Ver estado

```bash
docker compose ps
docker compose logs -f nginx-lb
docker compose logs -f web-en
docker compose logs -f web-es
docker compose logs -f db
docker compose logs -f stats
```

## Detener

```bash
docker compose down
```

Para borrar tambien datos persistentes de la base de datos:

```bash
docker compose down -v
```

No usar `down -v` en produccion salvo que se quiera eliminar la base de datos.

## Backup

```bash
./scripts/backup-db.sh
```

El respaldo queda en `backups/`.
