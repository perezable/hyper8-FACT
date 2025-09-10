#!/usr/bin/env python3
"""
Fix knowledge_export.json to ensure all entries have IDs.
"""

import json

# Load the current export
with open('data/knowledge_export.json', 'r') as f:
    data = json.load(f)

# Fix IDs for all entries
knowledge_base = data.get('knowledge_base', [])
for i, entry in enumerate(knowledge_base, start=1):
    if 'id' not in entry or entry['id'] is None:
        entry['id'] = i

# Save the fixed export
with open('data/knowledge_export_fixed.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Fixed {len(knowledge_base)} entries with proper IDs")
print(f"   First entry ID: {knowledge_base[0]['id'] if knowledge_base else 'N/A'}")
print(f"   Last entry ID: {knowledge_base[-1]['id'] if knowledge_base else 'N/A'}")

# Count entries by state
state_counts = {}
for entry in knowledge_base:
    state = entry.get('state', 'N/A')
    state_counts[state] = state_counts.get(state, 0) + 1

print("\nEntries by state:")
for state, count in sorted(state_counts.items()):
    print(f"  {state}: {count}")