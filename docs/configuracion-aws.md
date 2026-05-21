# Configuracion AWS

## Recursos recomendados

- Region: la mas cercana o la indicada por el profesor.
- VPC: `10.0.0.0/16`.
- Subred publica: `10.0.1.0/24`.
- Subred privada: `10.0.2.0/24`.
- Internet Gateway conectado a la VPC.
- Route table publica con `0.0.0.0/0` hacia Internet Gateway.
- Route table privada sin salida directa a Internet, o con NAT Gateway si se requiere instalar/actualizar paquetes desde instancias privadas.
- Elastic IP para el balanceador.
- Security Groups segun `docs/direccionamiento.md`.

Referencia AWS: una subred con ruta al Internet Gateway es publica; una sin esa ruta es privada. Ver documentacion oficial de Amazon VPC: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html

## Instancias EC2

### Balanceador

- AMI sugerida: Ubuntu Server LTS o Amazon Linux 2023.
- Tipo: `t2.micro` o `t3.micro` si aplica al Free Tier.
- Subred: publica `10.0.1.0/24`.
- IP publica: Elastic IP asociada.
- Security Group: `sg-lb`.
- Contenedor: `nginx-lb`.

### Web Server 1

- Subred: privada `10.0.2.0/24`.
- IP privada sugerida: `10.0.2.11`.
- Sin IP publica.
- Security Group: `sg-web`.
- Contenedor: `web-en`.

### Web Server 2

- Subred: privada `10.0.2.0/24`.
- IP privada sugerida: `10.0.2.12`.
- Sin IP publica.
- Security Group: `sg-web`.
- Contenedor: `web-es`.

### Base de datos

- Subred: privada `10.0.2.0/24`.
- IP privada sugerida: `10.0.2.20`.
- Sin IP publica.
- Security Group: `sg-db`.
- Contenedor: `db`.
- Volumen persistente Docker para `/var/lib/postgresql/data`.

### Estadisticas

- Puede ejecutarse como contenedor en una EC2 privada propia o junto a una de las EC2 internas.
- IP privada sugerida si esta separada: `10.0.2.30`.
- Security Group: `sg-stats`.
- Contenedor: `stats`.

## Instalacion base en cada EC2

Ejemplo para Ubuntu:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg openssl git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Cierre y vuelva a abrir la sesion SSH para aplicar el grupo `docker`.

## Despliegue con una EC2

Modo economico:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Proyecto-integrador-final-2026-1
cp .env.example .env
nano .env
./scripts/deploy.sh
```

Este modo publica solo el balanceador NGINX en `80` y `443`, y mantiene Flask/PostgreSQL sin puertos publicados.

## Despliegue con varias EC2

1. Clonar el repositorio en cada instancia o construir imagenes y subirlas a un registry.
2. En Web Server 1 ejecutar solo `web-en`.
3. En Web Server 2 ejecutar solo `web-es`.
4. En la instancia de base de datos ejecutar `db`.
5. En la instancia de stats ejecutar `stats`.
6. En el balanceador editar `nginx/nginx.conf` para usar IPs privadas reales:

```nginx
upstream backend_web {
    server 10.0.2.11:5000;
    server 10.0.2.12:5000;
}

upstream stats_app {
    server 10.0.2.30:5000;
}
```

7. Reiniciar NGINX:

```bash
docker compose restart nginx-lb
```

## Evidencias para capturas

- VPC y subredes.
- Route tables.
- Internet Gateway.
- Elastic IP del balanceador.
- Security Groups.
- Instancias EC2 con IP publica/privada.
- Contenedores corriendo con `docker compose ps`.
