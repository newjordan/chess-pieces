# ai-triposr-v1

Chess pieces reconstructed with TripoSR from SDXL concept renders.

- Module ID: `ai-triposr-v1`
- Author: Frosty40
- License: CC BY 4.0
- Format: GLB
- Shading: smooth
- Piece types: king, queen, rook, bishop, knight, pawn
- Sides: white and black share geometry. Each GLB embeds its own PBR material (`white` or `black`)
- Pose: Y-up, base on `y = 0`, footprint centered, asymmetric crowns face −Z
- Pipeline: SDXL image generation (ComfyUI), then TripoSR image-to-3D
- Poly stats: `mesh_stats.json` (measured from the GLBs)
- Manifest: `style.json`
- `previews/` are 768×768 renders of the white GLBs
- `references/` keeps the 1024×1024 concept renders used as reconstruction input

The reconstructions are uneven. The bishop, in particular, has a thin stem and a bulky mitre. Those artifacts are in the GLB; the reference stills show the source images.
