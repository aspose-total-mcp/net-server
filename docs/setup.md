# Setup and runtime configuration

Run `./scripts/setup.sh` from the repository root. Set `PYTHON=/path/to/python3.12` to choose an interpreter. It initializes `engine`, `plugins/words-net`, and `plugins/tex-net` without nested source submodules. The engine uses `.venv`; each standard-library plugin has its own `.venv`.

## Registration

Both plugins are already registered in the deployment catalog. `total-net.json` defines a .NET composition with Words and TeX and `owns_sources: false`. No shared context-engine repository change or extra registration is required.

Words supplies its retrieval profile; TeX has none and uses default behavior. `scripts/run-engine.sh` sets `ADCS_PRODUCT_PLUGIN_CATALOG` and `ADCS_RETRIEVAL_PLUGIN_CATALOG` to the deployment catalog and runs commands from `engine/`.

## Runtime stores

Follow the pinned engine's deployment guidance for PostgreSQL, Valkey, RabbitMQ, Qdrant, OpenSearch, authentication, and embeddings. Review `engine/.env.example` and create `engine/.env.local` with your settings. Use matching stores and embedding settings for API and ingestion workers. API symbol publication requires the structured symbol store to be enabled.

The engine's `make infra-up` provides development backing services. Review its environment and ports first. These host-Python helpers do not provision production infrastructure or include a product-specific Compose/Helm composition.

## Separate ingestion workspaces

Sources and ingestion state live under `workspaces/words` and `workspaces/tex`. They do not live under the `engine/` workspace used by the individual product server repositories. Gist caches live under each plugin's `sources/` directory. Use this repository's ingestion guide and wrappers consistently.

Queued workers must see these same absolute workspace paths and plugin interpreters. Keep component and source revisions stable while jobs are pending. For containers, provision the engine, catalogs, plugin files, interpreters, caches, and workspaces at paths visible to API and workers; the engine-only image does not bundle them.

## Expose the API

Use TLS, authentication, and suitable ingress configuration for external clients. Preserve MCP headers and streaming behavior. The README launch binds to loopback. Check `/healthz`, authenticated MCP initialization, and real product-specific retrieval after publication; health and fixture checks alone do not prove a corpus is live.
