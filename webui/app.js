const state = {
  config: null,
  assets: [],
  selected: new Set(),
  filter: "all",
};

const $ = (id) => document.getElementById(id);
const THEME_STORAGE_KEY = "unity-asset-classifier-theme";
const PRESET_COLORS = [
  "#2563eb",
  "#059669",
  "#db2777",
  "#7c3aed",
  "#0891b2",
  "#ea580c",
  "#dc2626",
  "#65a30d",
  "#ca8a04",
  "#64748b",
];
const SPECIAL_UNTAGGED_TAG = "태그 없음";

function applyTheme(theme) {
  const normalized = theme === "light" ? "light" : "dark";
  document.body.dataset.theme = normalized;
  $("themeToggleBtn").setAttribute("aria-pressed", normalized === "dark" ? "true" : "false");
  $("themeToggleText").textContent = normalized === "dark" ? "다크" : "라이트";
  localStorage.setItem(THEME_STORAGE_KEY, normalized);
}

function initTheme() {
  applyTheme(localStorage.getItem(THEME_STORAGE_KEY) || "dark");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `${res.status}`);
  return data;
}

function setStatus(text) {
  $("statusText").textContent = text;
}

function tagOptionsHtml(current = "") {
  const tags = state.config?.tags || [];
  return [
    `<option value="">미지정</option>`,
    ...tags.map((tag) => `<option value="${escapeHtml(tag.name)}" ${tag.name === current ? "selected" : ""}>${escapeHtml(tag.name)}</option>`),
  ].join("");
}

function filteredAssets() {
  if (state.filter === "vendor") return state.assets.filter((item) => item.vendor);
  if (state.filter === "root") return state.assets.filter((item) => !item.vendor);
  if (state.filter === "untagged") return state.assets.filter((item) => !item.tag);
  return state.assets;
}

function groupedAssets(items) {
  const groups = new Map();
  for (const item of items) {
    const groupName = item.status === "uncertain"
      ? "미확정"
      : item.vendor || "단일 에셋";
    if (!groups.has(groupName)) groups.set(groupName, []);
    groups.get(groupName).push(item);
  }
  return groups;
}

function renderConfig() {
  const cfg = state.config;
  $("assetsRootInput").value = cfg.assetsRoot;
  $("ignoredInput").value = cfg.ignoredTopFolders.join(", ");
  $("bulkTagSelect").innerHTML = tagOptionsHtml();
  $("presetColors").innerHTML = PRESET_COLORS.map((color) => `
    <button class="preset-btn" data-preset-color="${color}" title="${color}" style="background:${color}"></button>
  `).join("");
  $("tagList").innerHTML = cfg.tags.map((tag) => `
    <div class="tag-item">
      <input class="tag-color-input" type="color" value="${tag.color}" data-tag-color="${escapeHtml(tag.id)}" title="색상 수정" />
      <input class="tag-name-input" type="text" value="${escapeHtml(tag.name)}" data-tag-name="${escapeHtml(tag.id)}" title="이름 수정" ${tag.name === SPECIAL_UNTAGGED_TAG ? "readonly" : ""} />
      <button data-delete-tag="${escapeHtml(tag.id)}" title="삭제" ${tag.name === SPECIAL_UNTAGGED_TAG ? "disabled" : ""}>×</button>
    </div>
  `).join("");
}

function renderAssets() {
  const items = filteredAssets();
  $("emptyState").style.display = items.length ? "none" : "block";
  $("summaryText").textContent = summaryText();
  updateSelectAllState(items);
  const groups = groupedAssets(items);
  const html = [...groups.entries()].map(([groupName, groupItems]) => `
    <section class="group">
      <div class="group-title">
        <span>${escapeHtml(groupName)}</span>
        <span class="muted">${groupItems.length}</span>
        ${groupItems[0]?.vendor ? `<button class="group-action-btn" data-root-group="${escapeHtml(groupItems[0].vendor)}" type="button">단일 에셋으로 보기</button>` : ""}
      </div>
      ${groupItems.map(renderNode).join("")}
    </section>
  `).join("");
  $("treeRoot").innerHTML = html;
}

function updateSelectAllState(items = filteredAssets()) {
  const input = $("selectAllInput");
  const selectedCount = items.filter((item) => state.selected.has(item.id)).length;
  input.checked = items.length > 0 && selectedCount === items.length;
  input.indeterminate = selectedCount > 0 && selectedCount < items.length;
}

function renderNode(item) {
  const title = item.vendor ? `${item.vendor} / ${item.asset}` : item.asset;
  const markerText = (item.marker_dirs || []).slice(0, 4).join(", ");
  return `
    <div class="node">
      <input type="checkbox" data-select="${escapeHtml(item.id)}" ${state.selected.has(item.id) ? "checked" : ""} />
      <div class="node-name">
        <div class="node-title" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
        <div class="node-path" title="${escapeHtml(item.path)}">${escapeHtml(markerText || item.path)}</div>
      </div>
      <select data-tag-for="${escapeHtml(item.id)}">${tagOptionsHtml(item.tag)}</select>
    </div>
  `;
}

function summaryText() {
  const vendor = state.assets.filter((item) => item.vendor).length;
  const root = state.assets.filter((item) => !item.vendor).length;
  const tagged = state.assets.filter((item) => item.tag).length;
  return `전체 ${state.assets.length}개 | 판매자 그룹 ${vendor}개 | 단일 에셋 ${root}개 | 태그 지정 ${tagged}개`;
}

async function loadAll() {
  state.config = await api("/api/config");
  state.assets = await api("/api/assets");
  state.selected = new Set([...state.selected].filter((id) => state.assets.some((item) => item.id === id)));
  renderConfig();
  renderAssets();
  setStatus("스캔 완료");
}

async function saveConfig() {
  const payload = {
    ...state.config,
    assetsRoot: $("assetsRootInput").value.trim(),
    ignoredTopFolders: $("ignoredInput").value.split(",").map((item) => item.trim()).filter(Boolean),
  };
  await api("/api/config", { method: "POST", body: JSON.stringify(payload) });
  setStatus("설정 저장됨");
  await loadAll();
}

async function patchTag(id, tag) {
  await api(`/api/assets/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ tag }),
  });
  const item = state.assets.find((asset) => asset.id === id);
  if (item) item.tag = tag;
  renderAssets();
}

async function markGroupAsRootAsset(id) {
  await api("/api/groups/root-asset", {
    method: "POST",
    body: JSON.stringify({ id }),
  });
  state.selected.clear();
  setStatus(`${id} 그룹을 1차 폴더 에셋으로 변경`);
  await loadAll();
}

function selectedVendorGroupIds() {
  const ids = new Set();
  for (const selectedId of state.selected) {
    const item = state.assets.find((asset) => asset.id === selectedId);
    if (!item) continue;
    ids.add(item.vendor || item.id.split("/")[0]);
  }
  return [...ids];
}

async function markSelectedAsVendorGroups() {
  const ids = selectedVendorGroupIds();
  if (!ids.length) return;
  await api("/api/groups/vendor-group", {
    method: "POST",
    body: JSON.stringify({ ids }),
  });
  state.selected.clear();
  setStatus(`${ids.length}개 항목을 판매자 그룹으로 변경`);
  await loadAll();
}

async function organizeSelected() {
  const ids = [...state.selected];
  if (!ids.length) {
    setStatus("정리할 항목을 먼저 선택하세요");
    return;
  }
  const missing = ids.map((id) => state.assets.find((item) => item.id === id)).find((item) => item && !item.tag);
  if (missing) {
    setStatus(`태그 필요: ${missing.asset}`);
    return;
  }
  try {
    const results = await api("/api/organize", {
      method: "POST",
      body: JSON.stringify({ ids }),
    });
    const failed = results.filter((item) => item.error);
    state.selected.clear();
    const firstError = failed[0]?.error ? `: ${failed[0].error}` : "";
    setStatus(failed.length ? `${failed.length}개 실패${firstError}` : `${results.length}개 정리 완료`);
    await loadAll();
  } catch (error) {
    setStatus(`정리 실패: ${error.message}`);
  }
}

async function saveTags() {
  await api("/api/config", { method: "POST", body: JSON.stringify(state.config) });
  await loadAll();
}

async function renameTag(id, nextName) {
  const tag = state.config.tags.find((item) => item.id === id);
  if (!tag) return;
  if (tag.name === SPECIAL_UNTAGGED_TAG) {
    renderConfig();
    return;
  }
  if (nextName === SPECIAL_UNTAGGED_TAG) {
    renderConfig();
    setStatus("'태그 없음'은 기본 태그로만 사용됩니다");
    return;
  }
  const oldName = tag.name;
  tag.name = nextName;
  await saveTags();
  for (const asset of state.assets.filter((item) => item.tag === oldName)) {
    await patchTag(asset.id, tag.name);
  }
}

async function deleteTag(id) {
  state.config.tags = state.config.tags.filter((item) => item.id !== id || item.name === SPECIAL_UNTAGGED_TAG);
  await saveTags();
}

async function addTag() {
  const name = $("newTagNameInput").value.trim();
  if (!name) return;
  state.config.tags.push({
    id: crypto.randomUUID(),
    name,
    color: $("newTagColorInput").value,
  });
  $("newTagNameInput").value = "";
  await saveTags();
}

document.addEventListener("change", async (event) => {
  const target = event.target;
  if (target.matches("[data-select]")) {
    if (target.checked) state.selected.add(target.dataset.select);
    else state.selected.delete(target.dataset.select);
    updateSelectAllState();
  }
  if (target.matches("[data-tag-for]")) {
    await patchTag(target.dataset.tagFor, target.value);
  }
  if (target.matches("[data-tag-color]")) {
    const tag = state.config.tags.find((item) => item.id === target.dataset.tagColor);
    if (!tag) return;
    tag.color = target.value;
    await saveTags();
  }
  if (target.matches("[data-tag-name]")) {
    const nextName = target.value.trim();
    if (!nextName) {
      renderConfig();
      return;
    }
    await renameTag(target.dataset.tagName, nextName);
  }
});

document.addEventListener("click", async (event) => {
  const target = event.target;
  const node = target.closest(".node");
  if (node && !target.closest("input, select, button")) {
    const checkbox = node.querySelector("[data-select]");
    if (!checkbox) return;
    if (state.selected.has(checkbox.dataset.select)) {
      state.selected.delete(checkbox.dataset.select);
      checkbox.checked = false;
    } else {
      state.selected.add(checkbox.dataset.select);
      checkbox.checked = true;
    }
    return;
  }
  if (target.matches("[data-delete-tag]")) {
    await deleteTag(target.dataset.deleteTag);
  }
  if (target.matches("[data-preset-color]")) {
    $("newTagColorInput").value = target.dataset.presetColor;
  }
  if (target.matches("[data-root-group]")) {
    await markGroupAsRootAsset(target.dataset.rootGroup);
  }
});

document.querySelectorAll(".segmented button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".segmented button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.filter = button.dataset.filter;
    renderAssets();
  });
});

$("refreshBtn").addEventListener("click", loadAll);
$("selectAllInput").addEventListener("change", (event) => {
  const items = filteredAssets();
  if (event.target.checked) items.forEach((item) => state.selected.add(item.id));
  else items.forEach((item) => state.selected.delete(item.id));
  renderAssets();
});
$("themeToggleBtn").addEventListener("click", () => {
  applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
});
$("saveConfigBtn").addEventListener("click", saveConfig);
$("addTagBtn").addEventListener("click", addTag);
$("organizeBtn").addEventListener("click", organizeSelected);
$("vendorGroupBtn").addEventListener("click", markSelectedAsVendorGroups);
$("applyTagBtn").addEventListener("click", async () => {
  const tag = $("bulkTagSelect").value;
  for (const id of state.selected) {
    await patchTag(id, tag);
  }
  setStatus(`${state.selected.size}개 태그 적용`);
});

window.addEventListener("pagehide", () => {
  const payload = new Blob(["{}"], { type: "application/json" });
  if (navigator.sendBeacon) {
    navigator.sendBeacon("/api/shutdown", payload);
  } else {
    fetch("/api/shutdown", { method: "POST", body: "{}", headers: { "Content-Type": "application/json" }, keepalive: true }).catch(() => {});
  }
});

initTheme();
loadAll().catch((error) => setStatus(`오류: ${error.message}`));
