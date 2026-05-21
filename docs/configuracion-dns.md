# Configuracion DNS

## Objetivo

Crear un nombre publico que apunte a la IP publica del balanceador NGINX.

Flujo:

```text
www.dominio.com -> Registro A -> Elastic IP del balanceador
```

## Opciones gratuitas o academicas

Opciones revisadas en mayo de 2026:

- DuckDNS: subdominios gratuitos bajo `duckdns.org`. Sitio oficial: https://www.duckdns.org/
- No-IP Free Dynamic DNS: ofrece un hostname gratuito de entrada. Sitio oficial: https://www.noip.com/free
- FreeDNS afraid.org: ofrece DNS, subdominios y DNS dinamico gratuito. Sitio oficial: https://freedns.afraid.org/
- Freenom: puede aparecer como opcion de dominio gratuito, pero su disponibilidad ha sido irregular; verificar antes de depender de el. En mayo de 2026 su sitio oficial puede responder con mantenimiento o disponibilidad variable.
- Dominio institucional: usarlo si el profesor o la universidad lo permite.

Para una entrega de al menos tres meses, la recomendacion practica es DuckDNS o FreeDNS, o comprar un dominio economico si el equipo quiere evitar caducidades o verificaciones periodicas.

## Registro DNS requerido

Ejemplo con dominio propio:

| Tipo | Nombre | Valor | TTL |
|---|---|---|---|
| A | `www` | IP publica del balanceador | `300` o automatico |
| A | `@` | IP publica del balanceador | `300` o automatico |

Ejemplo con DuckDNS:

```text
proyecto-telematica.duckdns.org -> Elastic IP del balanceador
```

## Pasos generales

1. Crear cuenta en el proveedor DNS.
2. Crear subdominio o dominio.
3. Obtener la Elastic IP de la EC2 del balanceador.
4. Crear registro A hacia esa IP.
5. Esperar propagacion.

## Comprobaciones

```bash
nslookup www.dominio.com
ping www.dominio.com
curl -k https://www.dominio.com
```

Resultado esperado:

- `nslookup` devuelve la IP publica del balanceador.
- `ping` resuelve el nombre. Puede fallar respuesta ICMP si AWS lo bloquea; lo importante es que resuelva.
- `curl -k` carga HTML de una de las dos aplicaciones web.
