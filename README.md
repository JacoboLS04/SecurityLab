# Infraestructura · OPC Tickets 

Despliegue de `opc-tickets` (**SPA Angular + API Flask con alta disponibilidad**)
sobre **Docker Compose**, preparado y probado en **Debian 12** y **Rocky Linux 9**,
con **persistencia por Docker named volumes**.

Alcance: **§3.1** (balanceo con Docker) y **§3.2** (multi-distribución).

---

## Contexto

- **3 contenedores**: un balanceador Nginx (`opc-lb`) y **dos réplicas completas**
  de la app (`opc-app-1`, `opc-app-2`). Cada réplica sirve **el SPA y la API**.
- La **entrada pública** es `http://localhost:8080` → `opc-lb` reparte **todo**
  (`/`, el SPA, `/api`, `/adjuntos`) en round-robin.
- **Compose, no Swarm**: suficiente para el laboratorio y reproducible con
  `docker compose` a secas.
- Este directorio **consume `app-vulnerable/` casi intacto**. El único cambio es
  que `config.py` respeta la variable opcional `APP_DATA_DIR` para poder montar
  los volúmenes (sin ella, comportamiento original).

```
   Cliente ── http://<host>:8080 ─▶ opc-lb (Nginx no-root)
                                      │  /healthz → 200 (salud del lb)
                                      │  location / → upstream app1:5000 / app2:5000
                                      │  round-robin + cabecera X-Replica
                          ┌───────────┴───────────┐
                          ▼                        ▼
                    opc-app-1 (:5000)         opc-app-2 (:5000)
                      SPA + API Flask            SPA + API Flask
                      volume app-data-1          volume app-data-2
```
---

## Ejecución (VM, ruta recomendada)

> Comandos con `[HOST]` 

1. **Clonar y configurar** `[VM]`:
   ```bash
   git clone <URL-del-repo>
   cd <repo>/infraestructura
   cp .env.example .env       
   ```
6. **Levantar el stack** `[VM]`:
   ```bash
   docker compose up -d --build
   docker compose ps           
   ```

> El `--build` compila el SPA (Node 18) dentro de la imagen del backend y
> necesita **~1,5–2 GB de RAM** puntual. `down` conserva los volúmenes;
> `down -v` los borra.

### Alternativa: desplegar en tu propio host

Con Docker Desktop (Windows) o Docker Engine (Linux) funciona igual: `compose.yaml`
y los volúmenes son idénticos.

```bash
cd infraestructura && cp .env.example .env
docker compose up -d --build
```

---

## Verificación

```bash
# Interfaz y API responden a través del balanceador
curl -si http://localhost:8080/ | head -1            # 200 (SPA)
curl -s  http://localhost:8080/api/health             # {"status":"ok",...}
curl -s  http://localhost:8080/healthz                # ok (salud del lb)

# Balanceo: X-Replica alterna entre las dos réplicas
for i in $(seq 1 10); do curl -si http://localhost:8080/api/health | grep -i x-replica; done

# Log del balanceador: muestra a qué réplica fue cada petición ($upstream_addr)
docker compose logs lb | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:5000' | sort | uniq -c
```

**Failover** (cae una réplica; Nginx sirve desde la viva y reintenta):

```bash
docker compose stop app1
for i in $(seq 1 8); do curl -si http://localhost:8080/api/health | grep -i x-replica; done
docker compose start app1 && sleep 20
```

**Login real** (la app es funcional, no solo la API):

```bash
curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Optiplant2024!"}'
```

Plan de pruebas de carga/estrés completo en `../docs/infraestructura/pruebas-estres.md`.

---

## Persistencia

Cada réplica guarda sus datos en un **named volume propio** (`/app/data`):

| Volumen | Montado en | Contenido |
|---|---|---|
| `app-data-1` | `opc-app-1` | `tickets.db`, `adjuntos/`, exportaciones y logs |
| `app-data-2` | `opc-app-2` | ídem (independiente: SQLite no se comparte) |

Los datos sobreviven a `docker compose down` / `up -d` y desaparecen solo con
`down -v`.

---

## Estructura

```
infraestructura/
├── compose.yaml               # 2 réplicas (app completa) + Nginx + volúmenes
├── .env.example               # variables (copiar a .env)
├── deploy/nginx.conf          # balanceador (config completa, no-root)
├── docker/backend/
│   ├── Dockerfile             # compila el SPA (node:18) + API no-root
│   └── serve_with_spa.py      # sirve SPA + API sin tocar la app
├── scripts/setup_{debian,rocky}.sh   # preparación del SO
└── iso/                       # (optativo) ISOs de instalación
```

---

## Notas

- **Evidencia**: el repo **no incluye capturas**. Las pruebas se reproducen con los
  comandos de arriba y el informe (con **tus** umbrales) lo elaboras tú.
- **Pendiente**: capturas del despliegue dentro de las VMs Debian 12 y Rocky 9.
- **Más detalle**: redes y flujo de paquetes (`../docs/infraestructura/redes.md`),
  diseño de la opción "app completa por réplica"
  (`../docs/infraestructura/frontend-despliegue.md`,
  `../docs/infraestructura/como-funciona-el-balanceo.md`) y guía de cambios
  (`../docs/infraestructura/guia-cambios-y-pruebas.md`).
