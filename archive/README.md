# Archive - Old Versions

This folder contains previous versions of code that are no longer actively used but kept for reference.

## Files

### `graph_hitl_v1.py` (formerly `graph_hitl.py`)
- First implementation of Human-in-the-Loop functionality
- Used in: `run_hegemon.ipynb` (legacy notebook)
- Replaced by: `graph_hitl_v3.py`

### `graph_hitl_v2.py`
- Second iteration of HITL with improved checkpoint handling
- Used in: `run_hegemon.ipynb` (legacy notebook)
- Replaced by: `graph_hitl_v3.py`

## Current Active Versions

For current code, see main `hegemon/` folder:
- **`hegemon/graph.py`** - Base graph without HITL
- **`hegemon/graph_hitl_v3.py`** - Current HITL implementation with Simple UI support

## Why Archived?

These files were moved to keep the main codebase clean while preserving history for:
- Reference for development decisions
- Backwards compatibility if needed for old notebooks
- Learning from implementation evolution

## Using Old Versions

To use archived versions, update imports in old notebooks:

```python
# Old import (will break)
from hegemon.graph_hitl import create_hegemon_graph_hitl

# Fixed import
from archive.graph_hitl_v1 import create_hegemon_graph_hitl
```

**Recommendation:** Update to `graph_hitl_v3` for latest features and bug fixes.

---

**Last Updated:** 2025-10-22
