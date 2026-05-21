# Plan de pruebas

## Prueba 1: DNS

Comando:

```bash
nslookup www.dominio.com
```

Resultado esperado:

- El dominio resuelve a la IP publica del balanceador.

## Prueba 2: HTTPS

Desde navegador externo:

```text
https://www.dominio.com
```

Resultado esperado:

- Carga la aplicacion.
- El certificado es valido si se uso Let's Encrypt.

## Prueba 3: Round robin

Comandos:

```bash
curl -k https://www.dominio.com
curl -k https://www.dominio.com
curl -k https://www.dominio.com
curl -k https://www.dominio.com
```

Resultado esperado:

- Alternancia entre:
  - `Served by Web Server 1 - English`
  - `Atendido por Web Server 2 - Espanol`

## Prueba 4: Registro

Pasos:

1. Abrir la URL publica.
2. Registrar un usuario con nombre, comuna, fecha y carrera.
3. Repetir varias veces.

Resultado esperado:

- Aparece mensaje de confirmacion.
- Cada registro queda con identificador.

## Prueba 5: Base de datos

Comando:

```bash
docker compose exec db psql -U telematica_user -d telematica \
  -c "SELECT id, name, commune, program, language, entry_at, served_by FROM registrations ORDER BY id DESC;"
```

Resultado esperado:

- Se ven los registros enviados desde los formularios.

## Prueba 6: Estadisticas

URL:

```text
https://www.dominio.com/admin/stats
```

Resultado esperado:

- Total de usuarios.
- Grafica por comuna.
- Grafica por carrera.
- Tabla por comuna y carrera.
- Ultimos registros.

## Prueba 7: Correo

Requisitos:

- Variables SMTP configuradas en `.env`.
- Puerto SMTP permitido en reglas de salida.

Accion:

```text
Boton "Enviar estadisticas por correo"
```

Resultado esperado:

- El sistema informa envio exitoso.
- Llega reporte a `ialondonoo@eafit.edu.co`.

## Prueba 8: Simultaneidad

Opcion con curl:

```bash
for i in $(seq 1 20); do curl -k -s https://www.dominio.com >/dev/null & done; wait
```

Opcion con ApacheBench:

```bash
ab -n 100 -c 10 https://www.dominio.com/
```

Resultado esperado:

- NGINX responde sin errores.
- No se pierden registros.
- Los logs muestran trafico hacia ambos servidores.

## Script automatizado

```bash
./scripts/test.sh https://www.dominio.com
```

## Evidencias sugeridas

Guardar capturas en `docs/capturas/`:

- `01-dns.png`
- `02-https.png`
- `03-round-robin.png`
- `04-formulario.png`
- `05-db.png`
- `06-stats.png`
- `07-correo.png`
- `08-aws-security-groups.png`
