const state = {
  catalog: null,
  manifest: null,
  stats: null,
  styleIndex: 0,
  piece: "king",
  side: "white",
  view: null,
};

const piecesEl = document.querySelector("#pieces");
const stylesEl = document.querySelector("#styles");
const statusEl = document.querySelector("#view-status");
const nameEl = document.querySelector("#piece-name");
const statsEl = document.querySelector("#stats");
const noteEl = document.querySelector("#style-note");

function setStatus(message) {
  statusEl.hidden = !message;
  statusEl.textContent = message || "";
}

function currentStyle() {
  return state.catalog.styles[state.styleIndex];
}

async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function loadStyle() {
  const root = `../${currentStyle().path}`;
  state.manifest = await readJson(`${root}/style.json`);
  state.stats = await readJson(`${root}/${state.manifest.meshStats}`);
}

function renderStyleButtons() {
  stylesEl.replaceChildren();
  state.catalog.styles.forEach((style, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.role = "tab";
    button.textContent = style.name;
    button.setAttribute("aria-selected", String(index === state.styleIndex));
    button.addEventListener("click", async () => {
      if (index === state.styleIndex) {
        return;
      }
      state.styleIndex = index;
      state.piece = "king";
      try {
        await loadStyle();
        renderStyleButtons();
        renderPieceButtons();
        await showSelection();
      } catch (error) {
        setStatus(error.message);
      }
    });
    stylesEl.append(button);
  });
}

function renderPieceButtons() {
  const style = currentStyle();
  const root = `../${style.path}`;
  piecesEl.replaceChildren();
  for (const piece of state.manifest.pieces) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-current", String(piece === state.piece));
    const image = document.createElement("img");
    image.alt = `${style.name} ${piece}`;
    image.src = `${root}/${state.manifest.previews[piece]}`;
    const label = document.createElement("span");
    label.textContent = piece;
    const meta = document.createElement("small");
    const row = state.stats[piece];
    meta.textContent = row ? `${row.faces.toLocaleString()} faces` : "";
    button.append(image, label, meta);
    button.addEventListener("click", () => {
      state.piece = piece;
      renderPieceButtons();
      showSelection();
    });
    piecesEl.append(button);
  }
}

function renderStats() {
  const row = state.stats[state.piece];
  const style = currentStyle();
  nameEl.textContent = state.piece;
  statsEl.replaceChildren();
  const fields = [
    ["Vertices", row.vertices.toLocaleString()],
    ["Unique positions", row.uniquePositions.toLocaleString()],
    ["Faces", row.faces.toLocaleString()],
    ["Height", String(row.height)],
    ["Width", String(row.width)],
    ["Depth", String(row.depth)],
  ];
  for (const [label, value] of fields) {
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = value;
    statsEl.append(term, detail);
  }
  const shading = style.shading === "flat" ? "flat" : "smooth";
  noteEl.textContent = `${style.name} uses ${shading} shading. White and black share this geometry; the embedded material is the only difference.`;
}

async function showSelection() {
  renderStats();
  if (!state.view) {
    return;
  }
  const file = state.manifest.models[state.side][state.piece];
  const url = `../${currentStyle().path}/${file}`;
  setStatus("Loading mesh…");
  try {
    await state.view.load(url, currentStyle().shading === "flat");
    setStatus("");
  } catch (error) {
    setStatus(error.message);
  }
}

function bindSides() {
  for (const side of ["white", "black"]) {
    document.querySelector(`#side-${side}`).addEventListener("click", () => {
      state.side = side;
      for (const name of ["white", "black"]) {
        document.querySelector(`#side-${name}`).setAttribute("aria-pressed", String(name === side));
      }
      showSelection();
    });
  }
}

async function boot() {
  bindSides();
  try {
    state.catalog = await readJson("../catalog.json");
  } catch (error) {
    setStatus("Could not read catalog.json. From the repository root run: python -m chesscorpus preview");
    console.error(error);
    return;
  }
  try {
    await loadStyle();
  } catch (error) {
    setStatus(error.message);
    console.error(error);
    return;
  }
  renderStyleButtons();
  renderPieceButtons();
  renderStats();
  try {
    const { default: attach } = await import("./scene.js");
    state.view = attach(document.querySelector("#view"));
    await showSelection();
  } catch (error) {
    setStatus("The stills are local. The 3D view needs network access to load three.js.");
    console.error(error);
  }
}

boot();
