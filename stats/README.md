# Estadisticas y correo

La aplicacion `stats` expone:

- `GET /admin/stats`: tablero de estadisticas con graficas.
- `POST /admin/send-email`: envio del reporte a `SMTP_TO`.

## Variables SMTP

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@gmail.com
SMTP_PASSWORD=app_password
SMTP_FROM=correo@gmail.com
SMTP_TO=ialondonoo@eafit.edu.co
```

Si no se configuran credenciales SMTP, el boton de envio mostrara un error controlado, pero la aplicacion queda lista para enviar cuando se completen las variables.

## Seguridad del panel

Para activar proteccion basica por token:

```env
ADMIN_TOKEN=un_token_largo_y_privado
```

Luego ingrese a:

```text
https://www.dominio.com/admin/stats?token=un_token_largo_y_privado
```
