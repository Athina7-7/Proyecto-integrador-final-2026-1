# Informe Final — Proyecto Integrador de Telemática

## Portada

**Proyecto:** Despliegue de servicio telemático seguro en AWS  
**Materia:** Internet: Arquitectura y Protocolos / Telemática  
**Institución:** Universidad EAFIT  
**Integrantes:** Laura Indabur García y Athina Cappelletti Garcia   
**Fecha:** Mayo 2026  
**Repositorio GitHub:** [https://github.com/Athina7-7/Proyecto-integrador-final-2026-1]  
**URL pública:** `https://www.[dominio]`

---

## Tabla de Contenido

Debido a la extensión de la documentación, el informe se ha dividido en los siguientes módulos detallados. Haga clic en cada enlace para ver la información completa de esa sección:

### [1. Introducción y Arquitectura](01-introduccion-y-arquitectura.md)
* Objetivo del proyecto
* Descripción del problema
* Requisitos del enunciado
* Arquitectura del sistema y diagramas
* Tabla de direccionamiento de red y Security Groups

### [2. Configuración del Despliegue](02-configuracion-despliegue.md)
* Configuración AWS (VPC, Subredes, EC2)
* Configuración DNS
* Certificado HTTPS (Let's Encrypt / Autofirmado)
* Configuración Docker y `docker-compose.yml`

### [3. Documentación de las Aplicaciones](03-aplicaciones.md)
* Balanceador de carga — NGINX
* Aplicación Web Server 1 — Inglés (`web-en`)
* Aplicación Web Server 2 — Español (`web-es`)
* Aplicación de Reporte de Estadísticas (`stats`)
* Base de datos — PostgreSQL

### [4. Pruebas y Capturas](04-pruebas-y-capturas.md)
* Scripts de automatización
* Pruebas realizadas (DNS, HTTPS, Round-Robin, SMTP)
* Capturas de pantalla (Evidencias del funcionamiento)
* Problemas encontrados y soluciones
* Conclusiones
* Anexos y referencias

---

> **Nota para entrega:** Si se requiere unificar este documento en un solo PDF, se recomienda compilar los 4 archivos en el orden indicado y exportarlos como un único archivo `.pdf`.
