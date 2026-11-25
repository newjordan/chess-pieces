# Contributing

Thanks for adding to the corpus.

## Flow

1. Fork the repo and create a style folder at `styles/<style-id>/`.
2. Add the files required by `RULESET.md`.
3. Add the style to `catalog.json`.
4. Install the checker and run it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
chesscorpus validate
ruff check src tests
ruff format --check src tests
pytest
```

5. Open a pull request with the style id, the license, and any notes on poly count or toolchain.

If you change a GLB that is already in the repo, rewrite it with the shared pose before validating:

```bash
chesscorpus normalize
chesscorpus render
```

`normalize` stands the mesh on `y = 0`, centers the footprint, turns an asymmetric crown toward −Z, fixes inward winding, writes normals plus the side material, and refreshes `mesh_stats.json`. `render` replaces that style's preview PNGs from the white GLBs.

## What a review checks

`RULESET.md` is the policy. `chesscorpus validate` is the automated form of that policy: missing files, escaped paths, inward winding, a base that is not on `y = 0`, a preview that is not a 768×768 RGB PNG, and `mesh_stats.json` values that disagree with the GLB all fail the check.
