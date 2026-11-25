# Chess Pieces Corpus Ruleset

This ruleset keeps the repository public-friendly and modular. `chesscorpus validate` enforces the checks below.

## 1) Style module naming

- One style per folder: `styles/<style-id>/`
- `<style-id>` must be lowercase kebab-case and unique.

## 2) Required files per style module

```text
styles/<style-id>/
  style.json
  mesh_stats.json
  README.md
  models/
    white/{king,queen,rook,bishop,knight,pawn}.glb
    black/{king,queen,rook,bishop,knight,pawn}.glb
  previews/{king,queen,rook,bishop,knight,pawn}.png
```

Optional:

- `references/` for source stills that are not the loadable previews

## 3) Required global index update

`catalog.json` uses schema `1.1.0`. Every new style adds:

- `id`
- `name`
- `version`
- `path` (`styles/<style-id>`)
- `styleManifest` (`styles/<style-id>/style.json`)
- `license` (same string as `style.json`)
- `shading` (`flat` or `smooth`, same value as `style.json`)
- `pieceFormat` (`glb`)

## 4) `style.json` minimum schema

Each manifest includes:

- `id`, `name`, `version`
- `author`, `license`, `format` (`glb`)
- `shading` (`flat` or `smooth`)
- `orientation` set to `upAxis: "+Y"`, `base: "y=0"`, `center: "xz"`, `facing: "-Z"`
- `pieces`
- `models.white.*` and `models.black.*`
- `previews.*`
- `meshStats` set to `mesh_stats.json`

Paths are relative to the style folder and must not escape it.

## 5) Asset format, pose, and naming

- Model format: `.glb` only (glTF 2.0, one triangle mesh)
- Piece names are exactly `king`, `queen`, `rook`, `bishop`, `knight`, `pawn`
- Y is up, the lowest vertex is `y = 0`, and the footprint is centered on X and Z
- Y is the longest bounding-box axis
- Triangles wind outward and the file stores unit normals
- White and black share positions and indices
- Each side embeds a PBR material named `white` or `black`. White is the lighter material
- `flat` shading stores one vertex per corner, with one normal for that whole face
- `smooth` shading stores shared-vertex normals
- Previews are 768×768 RGB PNGs of the mesh, each under 400000 bytes

## 6) `mesh_stats.json`

One object per piece, measured from the white GLB:

- `vertices`, `faces`, `uniquePositions`
- `height` (Y extent), `width` (X extent), `depth` (Z extent), rounded to 4 decimal places

## 7) Style consistency

- A style reads as one visual family.
- White and black are the same family.
- Piece identities are recognizable.

## 8) Quality floor

Rejectable issues include:

- Broken meshes (holes, inverted winding, severe artifacts that hide the piece)
- Missing required files
- Ambiguous piece identity
- Inconsistent naming or paths
- A pose other than the one in section 5

## 9) Licensing and rights

- Submit only assets you have the right to publish.
- Name the license in the style `README.md` and in `style.json`.
- The modules already in this repo stay CC BY 4.0.
- Recommended licenses for new work: CC0, CC BY 4.0, or another permissive term.

## 10) PR checklist

- [ ] New style folder uses a valid `style-id`
- [ ] `style.json` is complete and its paths resolve
- [ ] 12 GLBs are present (6 white + 6 black) and match section 5
- [ ] 6 previews are present
- [ ] `mesh_stats.json` matches the white GLBs
- [ ] `catalog.json` is updated
- [ ] Style README names the author, license, and notes
- [ ] `chesscorpus validate` and `pytest` pass

Maintainers may request changes or reject submissions that do not follow this ruleset.
