# Proyecto Integrador Final - Telematica

Aplicacion web segura desplegable en AWS con Docker, NGINX, HTTPS, balanceo round robin, dos servidores web, PostgreSQL, estadisticas y envio de correo.

## Objetivo

Desplegar un servicio telematico en la nube que permita registrar usuarios interesados en estudiar una carrera, almacenar los datos en una base de datos, balancear trafico entre dos servidores web y generar estadisticas enviadas por correo a `ialondonoo@eafit.edu.co`.

## Componentes

- Cliente externo: navegador comercial en un computador fuera de AWS.
- Dominio publico con registro DNS tipo A hacia el balanceador.
- Balanceador NGINX en Docker con HTTPS y proxy inverso round robin.
- Web Server 1 en Docker: aplicacion fija en ingles.
- Web Server 2 en Docker: aplicacion fija en espanol.
- Base de datos PostgreSQL en Docker.
- Aplicacion de estadisticas en Docker con graficas y envio SMTP.
- Documentacion tecnica en `docs/`.

## Ejecucion rapida en laboratorio

1. Copiar variables:

```bash
cp .env.example .env
```

2. Generar un certificado autofirmado de prueba y levantar contenedores:

```bash
./scripts/deploy.sh
```

En Windows PowerShell:

```powershell
.\scripts\deploy.ps1
```

3. Abrir:

```text
https://localhost
https://localhost/admin/stats
```

El navegador mostrara advertencia si se usa certificado autofirmado. En AWS se debe usar Let's Encrypt o un certificado valido.

## Pruebas rapidas

```bash
./scripts/test.sh https://localhost
```

Para comprobar el balanceo:

```bash
curl -k https://localhost
curl -k https://localhost
curl -k https://localhost
```

La pagina debe alternar entre:

- `Served by Web Server 1 - English`
- `Atendido por Web Server 2 - Espanol`

## Documentacion

- [Informe final completo](docs/informe-final.md) — Contiene toda la documentacion del proyecto: arquitectura, direccionamiento, configuracion AWS, Docker, NGINX, DNS, HTTPS, aplicaciones web, estadisticas, pruebas y capturas.

## Nota de despliegue AWS

El `docker-compose.yml` incluido permite validar todos los componentes en una sola instancia EC2 o en un equipo local. Para una sustentacion estricta con varias VMs, se despliega cada contenedor en su EC2 correspondiente y en `nginx/nginx.conf` se reemplazan los nombres Docker `web-en` y `web-es` por las IP privadas de cada servidor web.
