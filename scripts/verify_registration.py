"""Verify pinned plugins, workspace isolation, extraction, and Total HTTP routing."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
catalog_path = ROOT / 'config/product-platform-plugins.json'
os.environ['ADCS_PRODUCT_PLUGIN_CATALOG'] = str(catalog_path)
os.environ['ADCS_RETRIEVAL_PLUGIN_CATALOG'] = str(catalog_path)
os.environ['ADCS_ENV'] = 'dev'
sys.path.insert(0, str(ROOT / 'engine/src'))
from adcs.plugins.catalog import PluginCatalog
from adcs.plugins.contracts import ExtractionResponse
from adcs.retrieval.profiles import load_profiles
from adcs.mcp.product_scope import TOTAL_NET_SCOPE

catalog = PluginCatalog(catalog_path)
expected = ['aspose.words.net', 'aspose.tex.net']
assert set(catalog.plugins) == set(expected)
assert set(catalog.compositions) == {'aspose.total.net'}
composition = catalog.compositions['aspose.total.net']
assert composition.members == expected
assert composition.language == 'net' and not composition.owns_sources
assert [(m.product_id, m.language) for m in TOTAL_NET_SCOPE.members] == [
    ('aspose.words', 'net'), ('aspose.tex', 'net')]
assert set(load_profiles(str(catalog_path))) == {('aspose.words', 'net')}
assert catalog.extractor('aspose.tex.net').retrieval_profile is None
resolved_sources = []
for product in ('words', 'tex'):
    manifest = catalog.extractor(f'aspose.{product}.net')
    plugin = ROOT / f'plugins/{product}-net'
    workspace = ROOT / 'workspaces' / product
    for source in manifest.sources.values():
        resolved = (workspace / source.path).resolve()
        assert resolved.is_relative_to(workspace.resolve())
        resolved_sources.append(resolved)
    for kind in ('docs', 'apiref'):
        source = manifest.sources[kind]
        if product == 'words':
            fixture = plugin / 'tests/fixtures' / ('docs.md' if kind == 'docs' else 'document-real.md')
            relative = source.prefix + ('/guide/_index.md' if kind == 'docs' else '/aspose.words/document/_index.md')
        else:
            relative = ('en/net/getting-started/supported-file-formats/_index.md' if kind == 'docs'
                        else 'english/net/aspose.tex/texjob/_index.md')
            fixture = plugin / 'tests/fixtures' / kind / relative
        request = dict(contract=manifest.contract, plugin_id=manifest.plugin_id,
                       product_id=manifest.product_id, language='net', operation='extract',
                       source_kind=kind, repo_id=source.repo_id, product_family='aspose',
                       source_path=source.path+'/'+relative, relative_repo_path=relative,
                       source_prefix=source.prefix, layout_detection=source.layout,
                       source_revision='deployment-fixture', canonical_base_url=source.canonical_base_url,
                       raw_markdown=fixture.read_text())
        interpreter = plugin / '.venv/bin/python'
        result = subprocess.run(catalog.command(manifest.plugin_id, python=str(interpreter)),
                                input=json.dumps(request), text=True, capture_output=True, check=True)
        response = ExtractionResponse.model_validate_json(result.stdout)
        assert response.plugin_id == manifest.plugin_id
        assert response.result.chunk_records
        if kind == 'apiref':
            expected_symbol = 'Aspose.Words.Document' if product == 'words' else 'Aspose.TeX.TeXJob'
            assert response.result.symbols[0].member_fqn == expected_symbol
assert len(set(resolved_sources)) == 4, 'Product source checkouts overlap'

from fastapi import FastAPI
from fastapi.testclient import TestClient
from adcs.api.mcp_gateway import router
from adcs.mcp.tool_gateway import MCPToolGateway
app = FastAPI()
app.include_router(router)
public = Mock()
public.query_docs.return_value.model_dump.return_value = {}
public.query_docs.return_value.results = []
public.query_docs.return_value.warnings = []
app.state.apiref_symbol_service = None
app.state.mcp_tool_gateway = MCPToolGateway(
    public_query_service=public, supported_revisions=('2025-11-25',), primary_revision='2025-11-25')
with TestClient(app) as client:
    def rpc(product, method, params=None):
        response = client.post(f'/{product}/net/mcp/v1/streamable-http', json={
            'jsonrpc':'2.0', 'id':1, 'method':method, 'params':params or {}})
        assert response.status_code == 200, response.text
        return response.json()

    for product in ('words', 'tex', 'total'):
        init = rpc(product, 'initialize')
        assert init['result']['serverInfo']['name'] == f'aspose-{product}-net-mcp'
        tools = rpc(product, 'tools/list')['result']['tools']
        assert tools
        for tool in tools:
            schema = tool['inputSchema']
            assert schema['properties']['language']['enum'] == ['net']
            assert schema['properties']['product_id']['enum'] == (
                ['aspose.words','aspose.tex'] if product == 'total' else [f'aspose.{product}'])
            if product == 'total':
                assert 'product_id' not in schema.get('required', [])
    def query(arguments):
        return rpc('total','tools/call',{'name':'query_docs','arguments':{'query':'conversion',**arguments}})
    result = query({})
    groups = result['result']['structuredContent']['results_by_product']
    assert [g['product_id'] for g in groups] == ['aspose.words','aspose.tex']
    assert [c.kwargs['request'].product_id for c in public.query_docs.call_args_list] == ['aspose.words','aspose.tex']
    assert all(c.kwargs['request'].language == 'net' and c.kwargs['allow_language_fallback'] is False
               for c in public.query_docs.call_args_list)
    for product in ('words','tex'):
        public.query_docs.reset_mock()
        assert 'result' in query({'product_id':f'aspose.{product}'})
        public.query_docs.assert_called_once()
        assert public.query_docs.call_args.kwargs['request'].product_id == f'aspose.{product}'
    for invalid in ({'product_id':'aspose.cells'}, {'product_id':'aspose.total'}, {'language':'cpp'}, {'language':'java'}):
        public.query_docs.reset_mock()
        assert query(invalid)['error']['code'] == -32602
        public.query_docs.assert_not_called()
print('Both plugin contracts, isolated workspaces, retrieval policies, MCP identities, Total fan-out and scope isolation verified')
