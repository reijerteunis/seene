# Seen

Seen ([tryseen.com](https://tryseen.com)) runs a brand's trading relationship with
online marketplaces end to end. It connects to Bol, Amazon, eBay, Kaufland and Otto
through their official APIs, keeps one reconciled trade record of orders, shipments,
returns and settlements, recovers the money the marketplaces kept in error, and then
takes over reconciliation, listing compliance, correspondence, pricing and advertising
as modules on the same record.

Start with [docs/prd/prd.md](docs/prd/prd.md) for what and why,
[docs/architecture.md](docs/architecture.md) for how,
[docs/development-plan.md](docs/development-plan.md) for when, and
[docs/harness/workflow.md](docs/harness/workflow.md) for how a ticket is worked.

## Where things run

**Development and the first pilots run on a laptop.** There is no cloud yet. Google
Cloud is provisioned only after Ruud records a go decision in the
[SEEN-007](docs/tickets/SEEN-007-go-live-on-google-cloud-after-the-go-no-go.md)
journal, and until then this repository's local Docker environment is the production
environment for anyone using the product.

**A pilot brand's data lives on the development machine.** If you open the tunnel
(`pnpm tunnel`) and hand a brand the URL, their orders, settlements and
correspondence are stored on that laptop and nowhere else: not backed up, not in the
EU region the architecture describes, and gone if the disk goes. Tell any pilot brand
this before they connect an account, and close the tunnel when the session ends. This
stops being true at go-live, not before.

## Getting it running

You need Docker (Docker Desktop, colima or Rancher), the
[Supabase CLI](https://supabase.com/docs/guides/cli), Node from `.nvmrc` and pnpm.
`cloudflared` as well, if you want the tunnel.

    git clone <this repository> && cd seene
    git config core.hooksPath .githooks     # the pre-commit gitleaks scan
    pnpm install
    cp .env.example .env.local
    pnpm dev:up                             # Supabase, Redis, Mailpit, the collector
    pnpm dev                                # api, worker, web

`pnpm dev:up` prints where each piece is listening. Fill in the Supabase keys with
`supabase status -o env`; they are generated per machine and belong in `.env.local`,
which is gitignored and is never committed.

`.env.local` is read at startup by `apps/api` and `apps/worker`, from the repository
root whatever directory you started them from, and by the test suite. A variable
already set in the environment wins, so a real deployment is never overridden by a
file that was left lying around. Marketplace credentials go in it as
`SEEN_SECRET_<reference shouted>`: the secrets provider reads
`SEEN_SECRET_BOL_NL_CLIENT_SECRET` for `bol/nl/client-secret`.

| | |
|---|---|
| api | <http://127.0.0.1:8080> (`/health`) |
| web | <http://127.0.0.1:3000> |
| Supabase Studio | <http://127.0.0.1:54323> |
| Supabase API | <http://127.0.0.1:54321> |
| Postgres | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` |
| Mailpit | <http://127.0.0.1:8025> (SMTP 1025) |
| Collector | OTLP on 4318, its own metrics on 8888 |
| Redis | `127.0.0.1:6379` |

### Commands

| | |
|---|---|
| `pnpm dev:up` | Starts every service. Safe to run again. |
| `pnpm dev:down` | Stops them. The database survives. |
| `pnpm db:reset` | Throws the database away and replays the migrations. |
| `pnpm dev` | Serves api, worker and web with watch. |
| `pnpm test` | The whole suite, against the running stack. |
| `pnpm replay:inbound` | Replays a Postmark inbound fixture into the local endpoint. |
| `pnpm tunnel` | Puts the local api on a public HTTPS URL. Read the warning above. |

### What it costs to run

Ten containers, about 800 MiB of memory between them. A 2 CPU, 4 GiB Docker VM holds
it with room. `supabase start` takes about 50 seconds the first time, while it pulls
its images, and about 25 seconds after that; the three compose services are healthy
within 10 seconds.

Supabase's `analytics`, `realtime` and `edge_runtime` are off in
`supabase/config.toml`. Analytics is Logflare plus a second Postgres and is most of
what makes the default stack heavy, and nothing in the product uses any of the three:
traces go to the collector, no subscription reads Postgres changes, and nothing runs
on Deno.

### If it will not start

**The Docker VM refuses to start** with `disk shrinking is not supported`: a colima
profile's disk size has drifted below the instance's actual disk. Neither
`colima start --disk N` nor `~/.colima/default/colima.yaml` fixes it; the file that
has to match is `~/.colima/_lima/<profile>/colima.yaml`.

**Supabase Studio will not start** with a `chown` permission error on
`supabase/snippets`: docker chowns a mount source path it creates itself and a
virtiofs mount denies it. `pnpm dev:up` creates the directory first, so this only
bites if you run `supabase start` by hand.

## The cloud is a configuration

Three things will be configured differently after go-live, and nothing else:

| | Now | After [SEEN-007](docs/tickets/SEEN-007-go-live-on-google-cloud-after-the-go-no-go.md) |
|---|---|---|
| `SEEN_SECRETS_PROVIDER` | `env`, from `.env.local` | `gcp-secret-manager` |
| `SEEN_STORAGE_PROVIDER` | `supabase`, the local stack | `gcs` |
| `SEEN_TELEMETRY_PROVIDER` | `console` or `otlp` | `cloud-logging` |

They live in `packages/providers`, which is the only package allowed to import a
cloud SDK. A test walks the tree and fails if one appears anywhere else, which is
what keeps go-live an infrastructure change rather than a refactor.

## Tests

`pnpm test` runs against the running stack, and
[.github/workflows/ci.yml](.github/workflows/ci.yml) starts the same
`docker-compose.yml` and the same `supabase/config.toml`, so a test that passes on a
laptop passes in CI for the same reasons. Bring the stack up before running it:
storage tests write to Supabase, mail tests send through Mailpit and read the message
back, and telemetry tests ask the collector what it accepted.

No test ever calls a live marketplace.
