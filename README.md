# Aspose.Total for .NET MCP Server

One context engine serving **Aspose.Words for .NET and Aspose.TeX for .NET** through a Total MCP endpoint. This deployment currently covers these two products only; it does not include every Aspose.Total component.

Total is a serving composition, not another extractor or corpus. Ingest each product separately, then query both through `/total/net/mcp/v1/streamable-http`. Omitting `product_id` searches the member products independently; selecting `aspose.words` or `aspose.tex` narrows the request. Results remain product-scoped and .NET-only.

[Setup](docs/setup.md) · [Ingestion](docs/ingestion.md) · [Clients](docs/clients.md) · [Maintenance](docs/public-release.md)

## Project family

| Repository | Responsibility |
| --- | --- |
| [context-engine](https://github.com/aspose-core-mcp/context-engine) | Shared ingestion, indexing, retrieval, and MCP infrastructure |
| [Words/.NET plugin](https://github.com/aspose-words-mcp/net-plugin) | Words extraction and retrieval profile |
| [TeX/.NET plugin](https://github.com/aspose-tex-mcp/net-plugin) | TeX extraction with default engine retrieval behavior |
| [Total/.NET server](https://github.com/aspose-total-mcp/net-server) **(this repository)** | Pinned engine, both plugins, and Total composition |

## Get started

Requires Git and Python 3.12 or newer:

```sh
git clone https://github.com/aspose-total-mcp/net-server.git
cd net-server
./scripts/setup.sh
```

Setup initializes only the immediate engine/plugin submodules, installs engine dependencies, creates separate plugin interpreters and ingestion workspaces, and verifies registration, extraction, and MCP routing. Do not clone recursively: legacy engine source submodules are not needed. Setup does not provision stores, download corpora, or publish indexes.

Configure runtime services, credentials, and embeddings using [setup](docs/setup.md), then launch:

```sh
./scripts/run-engine.sh -m uvicorn adcs.api.main:app --host 127.0.0.1 --port 8080
# Separate terminal for queued ingestion:
./scripts/run-engine.sh -m celery -A adcs.worker.celery_app:celery_app worker --loglevel=info
```

Follow [source preparation and ingestion](docs/ingestion.md), then connect a client to your deployment:

```text
https://YOUR_MCP_HOST/total/net/mcp/v1/streamable-http
```

Words and TeX endpoints remain available on the same process. Other inherited compatibility routes remain defined; restrict exposed paths at ingress if needed. No hosted endpoint is provided.

## Registration and workspaces

`config/product-platform-plugins.json` registers both public plugins and `config/total-net.json` selects exactly those two members. The shared engine's default catalog stays unchanged. The launch wrapper sets both catalog environment variables.

Each plugin retains its published manifest. Because both use `sources/api-reference`, ingestion uses **separate workspaces**: `workspaces/words/` and `workspaces/tex/`. Each plugin keeps its own Gist cache. Both products publish to shared runtime stores with distinct product/language metadata. Never ingest `aspose.total.net` as a third product.

## Validation and maintenance

GitHub CI checks shell syntax, catalogs, both plugin suites, extraction contracts, endpoint identities, Total fan-out, product selection, and rejection of unsupported scopes. These checks use fixtures and mocked retrieval; verify actual indexed citations after deployment.

Gitlinks pin reviewed public component commits. Upstream releases do not update this deployment automatically. See [maintenance](docs/public-release.md).

## License

[MIT](LICENSE), copyright (c) 2001-2026 Aspose Pty Ltd. Preserve the licenses and notices of the pinned engine and plugins when distributing them.
