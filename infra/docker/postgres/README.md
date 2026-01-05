# ZeroUI Postgres (Docker) — Option A (3 Databases)

## What this creates
One Postgres container hosting three separate databases:
- zeroui_tenant_pg (user: zeroui_tenant_user)
- zeroui_product_pg (user: zeroui_product_user)
- zeroui_shared_pg (user: zeroui_shared_user)

Each DB gets:
- schema `app` owned by its user
- CREATE revoked on schema `public` for PUBLIC

## Setup (PowerShell)
From repo root:

1) Create your local env file (do NOT commit secrets):
   Copy-Item infra/docker/postgres/postgres.env.example infra/docker/postgres/postgres.env

2) Start Postgres:
   cd infra/docker/postgres
   docker compose -f compose.yaml up -d

3) Watch logs (first boot runs init scripts):
   docker logs -f zeroui-postgres

## Verify (PowerShell)
List databases:
  docker exec -it zeroui-postgres psql -U postgres -d postgres -c "\l"

List roles:
  docker exec -it zeroui-postgres psql -U postgres -d postgres -c "\du"

Check each DB has schema app:
  docker exec -it zeroui-postgres psql -U postgres -d zeroui_tenant_pg  -c "\dn"
  docker exec -it zeroui-postgres psql -U postgres -d zeroui_product_pg -c "\dn"
  docker exec -it zeroui-postgres psql -U postgres -d zeroui_shared_pg  -c "\dn"

## Important
Init scripts in /docker-entrypoint-initdb.d run ONLY when the data directory is empty.
If you change init scripts and need them to re-run, wipe the volume:

  cd infra/docker/postgres
  docker compose -f compose.yaml down -v
  docker compose -f compose.yaml up -d

## Port conflicts
If port 5432 is already in use on your machine, change the host-side port in compose.yaml:
- "5432:5432" -> "54321:5432"
Then connect using localhost:54321.

