import json
from pathlib import Path

# Step B3: Save semantic extraction
new_data = json.loads(Path('.graphify_semantic_new.json').read_text()) if Path('.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}

# Load cached data
cached = json.loads(Path('.graphify_cached.json').read_text()) if Path('.graphify_cached.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}

# Merge cached + new
all_nodes = cached['nodes'] + new_data.get('nodes', [])
all_edges = cached['edges'] + new_data.get('edges', [])
all_hyperedges = cached.get('hyperedges', []) + new_data.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {
    'nodes': deduped,
    'edges': all_edges,
    'hyperedges': all_hyperedges,
    'input_tokens': new_data.get('input_tokens', 0),
    'output_tokens': new_data.get('output_tokens', 0),
}
Path('.graphify_semantic.json').write_text(json.dumps(merged, indent=2))
print(f'Semantic: {len(deduped)} nodes, {len(all_edges)} edges ({len(cached["nodes"])} cached + {len(new_data.get("nodes",[]))} new)')
