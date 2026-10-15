const sourceEditor = document.querySelector("#sourceEditor");
const frameworkPreview = document.querySelector("#frameworkPreview");
const appStatus = document.querySelector("#appStatus");
const frameworkState = document.querySelector("#frameworkState");
const draftState = document.querySelector("#draftState");
const sourceMessage = document.querySelector("#sourceMessage");
const resultMessage = document.querySelector("#resultMessage");
const resultBody = document.querySelector("#resultBody");
const resultTitle = document.querySelector("#resultTitle");
const resultTag = document.querySelector("#resultTag");
const resultCount = document.querySelector("#resultCount");
const actionButtons = [...document.querySelectorAll(".action-button")];

const state = {
  activeText: "",
  activeFramework: null,
  activeName: "éditeur",
  derivedSource: "",
  busy: false,
};

const actionTitles = {
  arguments: "Arguments et attaques",
  properties: "Propriétés structurelles",
  noncircular: "Transformation non circulaire",
  atomic: "Transformation atomique",
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Le serveur a renvoyé une réponse illisible.");
  }
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "La requête n'a pas abouti.");
  }
  return data;
}

function setStatus(message) {
  appStatus.textContent = message;
}

function showMessage(element, message, kind = "") {
  element.textContent = message;
  element.classList.toggle("is-error", kind === "error");
  element.classList.toggle("is-success", kind === "success");
}

function setBusy(isBusy, message = "") {
  state.busy = isBusy;
  resultBody.setAttribute("aria-busy", String(isBusy));
  resultBody.classList.toggle("is-busy", isBusy);
  actionButtons.forEach((button) => {
    button.disabled = isBusy || !state.activeText;
  });
  if (message) setStatus(message);
}

function updateDraftState() {
  const changed = Boolean(state.activeText) && sourceEditor.value !== state.activeText;
  draftState.textContent = changed ? "Brouillon modifié" : "Synchronisé";
  draftState.classList.toggle("is-dirty", changed);
  if (changed) {
    frameworkState.textContent = "Modifications à valider";
    frameworkState.className = "state-badge";
  } else if (state.activeText) {
    frameworkState.textContent = "Framework validé";
    frameworkState.className = "state-badge is-ready";
  }
}

function setActiveFramework(text, name, payload, updateEditor = true) {
  state.activeText = text;
  state.activeName = name;
  state.activeFramework = payload;
  if (updateEditor) sourceEditor.value = text;
  frameworkPreview.textContent = payload.display;
  frameworkState.textContent = "Framework validé";
  frameworkState.className = "state-badge is-ready";
  showMessage(sourceMessage, `${name} chargé.`, "success");
  updateDraftState();
  actionButtons.forEach((button) => { button.disabled = state.busy; });
}

function setInvalidFramework(message) {
  frameworkState.textContent = "Brouillon invalide";
  frameworkState.className = "state-badge is-error";
  showMessage(sourceMessage, message, "error");
}

async function validateAndActivate(text, name, updateEditor = true) {
  const data = await requestJson("/api/validate", {
    method: "POST",
    body: JSON.stringify({ text, name }),
  });
  setActiveFramework(text, name, data.framework, updateEditor);
  setStatus(`${name} prêt`);
  return data.framework;
}

async function openExample() {
  const filename = document.querySelector("#exampleSelect").value;
  setBusy(true, "Ouverture de l’exemple…");
  showMessage(sourceMessage, "");
  try {
    const response = await fetch(`/api/examples/${encodeURIComponent(filename)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "L’exemple ne peut pas être chargé.");
    await validateAndActivate(data.text, data.name);
    showMessage(resultMessage, "");
  } catch (error) {
    showMessage(sourceMessage, error.message, "error");
    setStatus("Échec du chargement");
  } finally {
    setBusy(false);
  }
}

async function importFile(file) {
  if (!file) return;
  if (file.size > 64 * 1024) {
    showMessage(sourceMessage, "Le fichier dépasse la limite de 64 Ko.", "error");
    return;
  }
  setBusy(true, "Lecture du fichier…");
  try {
    const buffer = await file.arrayBuffer();
    const text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
    await validateAndActivate(text, file.name);
    showMessage(resultMessage, "");
  } catch (error) {
    showMessage(sourceMessage, error.message || "Le fichier doit être encodé en UTF-8.", "error");
    setStatus("Échec de l’import");
  } finally {
    setBusy(false);
    document.querySelector("#frameworkFile").value = "";
  }
}

async function importUrl() {
  const urlField = document.querySelector("#frameworkUrl");
  const url = urlField.value.trim();
  if (!url) {
    showMessage(sourceMessage, "Saisissez une URL HTTP(S) publique.", "error");
    urlField.focus();
    return;
  }
  setBusy(true, "Téléchargement du framework…");
  try {
    const data = await requestJson("/api/import-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
    await validateAndActivate(data.text, new URL(url).pathname.split("/").pop() || "URL");
    showMessage(resultMessage, "");
  } catch (error) {
    showMessage(sourceMessage, error.message, "error");
    setStatus("Échec de l’import URL");
  } finally {
    setBusy(false);
  }
}

function renderEmptyList(message) {
  return `<div class="empty-list">${escapeHtml(message)}</div>`;
}

function argumentId(argument) {
  return JSON.stringify([argument.conclusion, argument.support]);
}

function shortLabel(value, limit) {
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
}

function renderArgumentGraph(data) {
  if (!data.arguments.length) return renderEmptyList("Aucun argument à représenter.");

  const columns = Math.min(3, data.arguments.length);
  const rows = Math.ceil(data.arguments.length / columns);
  const width = columns * 240 + 40;
  const height = rows * 140 + 30;
  const nodeWidth = 204;
  const nodeHeight = 76;
  const positions = new Map();
  data.arguments.forEach((argument, index) => {
    positions.set(argumentId(argument), {
      x: 120 + (index % columns) * 240,
      y: 65 + Math.floor(index / columns) * 140,
    });
  });

  const edges = data.attacks.map((attack, index) => {
    const source = positions.get(argumentId(attack.attacker));
    const target = positions.get(argumentId(attack.target));
    if (!source || !target) return "";
    const kind = attack.kind === "inversée" ? "reversed" : "normal";
    if (source === target) {
      const startX = source.x - 30;
      const endX = source.x + 30;
      const top = source.y - nodeHeight / 2;
      return `<path class="graph-edge ${kind}" d="M ${startX} ${top} C ${startX - 48} ${top - 72}, ${endX + 48} ${top - 72}, ${endX} ${top}" marker-end="url(#attackArrow-${kind})"><title>${escapeHtml(attack.kind)} : ${escapeHtml(attack.attacker.label)} vers ${escapeHtml(attack.target.label)}</title></path>`;
    }
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.hypot(dx, dy);
    const ux = dx / distance;
    const uy = dy / distance;
    const startOffset = Math.min(nodeWidth / 2 / (Math.abs(ux) || Number.EPSILON), nodeHeight / 2 / (Math.abs(uy) || Number.EPSILON));
    const endOffset = startOffset;
    const startX = source.x + ux * startOffset;
    const startY = source.y + uy * startOffset;
    const endX = target.x - ux * endOffset;
    const endY = target.y - uy * endOffset;
    const curve = ((index % 5) - 2) * 14;
    const controlX = (startX + endX) / 2 - uy * curve;
    const controlY = (startY + endY) / 2 + ux * curve;
    return `<path class="graph-edge ${kind}" d="M ${startX} ${startY} Q ${controlX} ${controlY}, ${endX} ${endY}" marker-end="url(#attackArrow-${kind})"><title>${escapeHtml(attack.kind)} : ${escapeHtml(attack.attacker.label)} vers ${escapeHtml(attack.target.label)}</title></path>`;
  }).join("");

  const nodes = data.arguments.map((argument) => {
    const { x, y } = positions.get(argumentId(argument));
    const support = argument.support.join(", ") || "∅";
    return `<g class="graph-node" transform="translate(${x} ${y})"><title>${escapeHtml(argument.label)}</title><rect x="-${nodeWidth / 2}" y="-${nodeHeight / 2}" width="${nodeWidth}" height="${nodeHeight}" rx="3"></rect><text class="graph-conclusion" text-anchor="middle" y="-5">${escapeHtml(shortLabel(argument.conclusion, 23))}</text><text class="graph-support" text-anchor="middle" y="17">${escapeHtml(shortLabel(`support : ${support}`, 28))}</text></g>`;
  }).join("");

  return `<div class="graph-shell">
    <div class="graph-legend" aria-label="Légende des attaques">
      <span><i class="legend-line normal" aria-hidden="true"></i>Attaque normale</span>
      <span><i class="legend-line reversed" aria-hidden="true"></i>Attaque inversée</span>
    </div>
    <div class="graph-scroll" role="region" aria-label="Graphe des arguments ABA" tabindex="0">
      <svg class="argument-graph" viewBox="0 0 ${width} ${height}" role="img" aria-label="${data.arguments.length} arguments et ${data.attacks.length} attaques">
        <defs>
          <marker id="attackArrow-normal" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker>
          <marker id="attackArrow-reversed" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker>
        </defs>
        ${edges || ""}${nodes}
      </svg>
    </div>
    ${data.attacks.length ? "" : `<p class="graph-note">Aucune attaque dans ce framework.</p>`}
  </div>`;
}

function renderArguments(data) {
  const argumentsHtml = data.arguments.length
    ? data.arguments.map((argument) => `
        <article class="argument-row">
          <div class="argument-main">
            <span class="conclusion">${escapeHtml(argument.conclusion)}</span>
            <span class="support-text"><span class="support-label">support</span> ${escapeHtml(argument.support.join(", ") || "∅")}</span>
          </div>
        </article>`).join("")
    : renderEmptyList("Aucun argument calculé.");
  const attacksHtml = data.attacks.length
    ? data.attacks.map((attack) => `
        <article class="attack-row">
          <div class="attack-main">
            <span class="conclusion">${escapeHtml(attack.attacker.label)}</span>
            <span class="attack-target">cible : ${escapeHtml(attack.target.label)}</span>
          </div>
          <span class="attack-kind">${escapeHtml(attack.kind)}</span>
        </article>`).join("")
    : renderEmptyList("Aucune attaque calculée.");
  resultBody.innerHTML = `
    <div class="result-tabs" role="tablist" aria-label="Résultats arguments et attaques">
      <button class="result-tab is-active" data-view="graph" role="tab" aria-selected="true" type="button">Graphe</button>
      <button class="result-tab" data-view="arguments" role="tab" aria-selected="false" type="button">Arguments · ${data.arguments.length}</button>
      <button class="result-tab" data-view="attacks" role="tab" aria-selected="false" type="button">Attaques · ${data.attacks.length}</button>
    </div>
    <div class="result-list" data-list="graph">${renderArgumentGraph(data)}</div>
    <div class="result-list" data-list="arguments" hidden>${argumentsHtml}</div>
    <div class="result-list" data-list="attacks" hidden>${attacksHtml}</div>`;
  document.querySelectorAll(".result-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".result-tab").forEach((item) => {
        const selected = item === tab;
        item.classList.toggle("is-active", selected);
        item.setAttribute("aria-selected", String(selected));
      });
      document.querySelectorAll("[data-list]").forEach((list) => {
        list.hidden = list.dataset.list !== tab.dataset.view;
      });
    });
  });
}

function renderProperties(properties) {
  const rows = [
    ["Framework atomique", properties.atomic],
    ["Framework circulaire", properties.circular],
  ];
  resultBody.innerHTML = `<div class="property-list">${rows.map(([name, value]) => `
    <div class="property-row">
      <span class="property-name">${name}</span>
      <span class="property-value ${value ? "is-yes" : "is-no"}">${value ? "Oui" : "Non"}</span>
    </div>`).join("")}</div>`;
}

function renderTransformation(data) {
  const isChanged = data.transformed;
  const kind = data.action === "atomic" ? "atomique" : "non circulaire";
  resultTitle.textContent = data.action === "noncircular" && !isChanged
    ? "Déjà non circulaire"
    : `Framework ${kind} dérivé`;
  resultTag.textContent = isChanged ? "DÉRIVÉ" : "INCHANGÉ";
  state.derivedSource = data.framework.source;
  resultBody.innerHTML = `
    <pre class="transformed-framework">${escapeHtml(data.framework.display)}</pre>
    <div class="reuse-row">
      <button class="button button-light" id="reuseDerivedButton" type="button">Utiliser comme nouvelle source</button>
    </div>`;
  document.querySelector("#reuseDerivedButton").addEventListener("click", async () => {
    try {
      await validateAndActivate(state.derivedSource, "Framework dérivé");
      document.querySelector("#editorTab").click();
      showMessage(resultMessage, "Le framework dérivé est maintenant la source active.", "success");
    } catch (error) {
      showMessage(resultMessage, error.message, "error");
    }
  });
}

function renderResult(data) {
  resultTitle.textContent = actionTitles[data.action];
  resultTag.textContent = "TERMINÉ";
  resultCount.textContent = data.action === "arguments"
    ? `${data.arguments.length} ARG. · ${data.attacks.length} ATT.`
    : "ANALYSÉ";
  if (data.action === "arguments") renderArguments(data);
  if (data.action === "properties") renderProperties(data.properties);
  if (data.action === "noncircular" || data.action === "atomic") renderTransformation(data);
}

async function runAction(action) {
  setBusy(true, "Calcul en cours…");
  showMessage(sourceMessage, "");
  showMessage(resultMessage, "");
  try {
    const data = await requestJson("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ text: sourceEditor.value, name: state.activeName, action }),
    });
    setActiveFramework(sourceEditor.value, state.activeName, data.input_framework, false);
    renderResult(data);
    showMessage(sourceMessage, "Framework source validé.", "success");
    setStatus("Analyse terminée");
  } catch (error) {
    setInvalidFramework(error.message);
    resultTitle.textContent = "Analyse impossible";
    resultTag.textContent = "ERREUR";
    resultBody.innerHTML = `<div class="empty-list">${escapeHtml(error.message)}</div>`;
    showMessage(resultMessage, error.message, "error");
    setStatus("Vérifiez le framework");
  } finally {
    setBusy(false);
  }
}

function switchSourceTab(tabName) {
  const editorSelected = tabName === "editor";
  document.querySelector("#sourceEditor").hidden = !editorSelected;
  document.querySelector("#frameworkPreview").hidden = editorSelected;
  document.querySelector("#editorTab").classList.toggle("is-active", editorSelected);
  document.querySelector("#previewTab").classList.toggle("is-active", !editorSelected);
  document.querySelector("#editorTab").setAttribute("aria-selected", String(editorSelected));
  document.querySelector("#previewTab").setAttribute("aria-selected", String(!editorSelected));
}

document.querySelector("#loadExampleButton").addEventListener("click", openExample);
document.querySelector("#exampleSelect").addEventListener("change", openExample);
document.querySelector("#chooseFileButton").addEventListener("click", () => {
  document.querySelector("#frameworkFile").click();
});
document.querySelector("#frameworkFile").addEventListener("change", (event) => {
  importFile(event.target.files[0]);
});
document.querySelector("#loadUrlButton").addEventListener("click", importUrl);
document.querySelector("#frameworkUrl").addEventListener("keydown", (event) => {
  if (event.key === "Enter") importUrl();
});
document.querySelector("#validateButton").addEventListener("click", async () => {
  setBusy(true, "Validation du framework…");
  try {
    await validateAndActivate(sourceEditor.value, "éditeur", false);
    showMessage(resultMessage, "");
  } catch (error) {
    setInvalidFramework(error.message);
    setStatus("Framework invalide");
  } finally {
    setBusy(false);
  }
});
sourceEditor.addEventListener("input", updateDraftState);
document.querySelector("#editorTab").addEventListener("click", () => switchSourceTab("editor"));
document.querySelector("#previewTab").addEventListener("click", () => switchSourceTab("preview"));
actionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    actionButtons.forEach((item) => item.classList.toggle("is-selected", item === button));
    runAction(button.dataset.action);
  });
});

openExample();