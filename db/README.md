# Base de datos

Motor: PostgreSQL en Docker.

## Configuracion por defecto

- Base de datos: `telematica`
- Usuario: `telematica_user`
- Puerto interno: `5432`
- Puerto expuesto al host: ninguno
- Volumen persistente: `db_data`
- Script inicial: `db/init.sql`

## Tabla principal

```sql
CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    commune VARCHAR(20) NOT NULL,
    program VARCHAR(50) NOT NULL,
    language VARCHAR(20) NOT NULL,
    entry_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    served_by VARCHAR(50),
    client_ip VARCHAR(80)
);
```

## Comprobar datos

```bash
docker compose exec db psql -U telematica_user -d telematica \
  -c "SELECT id, name, commune, program, language, entry_at, served_by FROM registrations ORDER BY id DESC;"
```
