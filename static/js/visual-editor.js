(() => {
  "use strict";

  const dataNode = document.getElementById("avan-visual-design-data");
  if (!dataNode || window.__avanVisualStudioV2Initialized) return;
  window.__avanVisualStudioV2Initialized = true;

  let pageData = {};
  try { pageData = JSON.parse(dataNode.textContent || "{}"); } catch (_) {}

  const API = "/owner/design/api/";
  const UPLOAD_API = "/owner/design/upload/";
  const pagePath = window.location.pathname;
  const launches = [...document.querySelectorAll("[data-avan-visual-open]")];

  // These routes remain outside the visual editor even for the owner.
  const blockedPrefixes = ["/owner/", "/admin/", "/api/", "/bag/", "/checkout/", "/orders/", "/payments/"];
  if (blockedPrefixes.some(prefix => pagePath.startsWith(prefix))) {
    launches.forEach(button => button.hidden = true);
    return;
  }

  const STYLE_KEYS = [
    "color", "backgroundColor", "fontSize", "fontWeight", "textAlign",
    "borderRadius", "padding", "margin", "maxWidth", "width", "height",
    "minHeight", "letterSpacing", "lineHeight", "opacity", "objectFit"
  ];

  let active = new Map();
  let selected = null;
  let selectedKey = null;
  let editMode = false;
  let history = [];
  let historyIndex = -1;
  let busy = false;
  let dirty = false;
  const baseline = new Map();

  const pathKey = path => "path:" + JSON.stringify(path || []);
  const itemKey = item => item.kind === "insert" ? "insert:" + item.id : pathKey(item.path);

  function nodePath(element) {
    const parts = [];
    let node = element;
    while (node && node !== document.body && parts.length < 16) {
      if (!node.parentElement) break;
      const tag = node.tagName.toLowerCase();
      const siblings = [...node.parentElement.children].filter(item => item.tagName === node.tagName);
      parts.unshift({ tag, index: siblings.indexOf(node) + 1 });
      node = node.parentElement;
    }
    return parts.length ? parts : null;
  }

  function resolve(parts) {
    let parent = document.body;
    let current = null;
    for (const part of parts || []) {
      if (!parent) return null;
      const siblings = [...parent.children].filter(item => item.tagName.toLowerCase() === part.tag);
      current = siblings[part.index - 1] || null;
      parent = current;
    }
    return current;
  }

  function captureBaseline(element, path) {
    const k = pathKey(path);
    if (baseline.has(k)) return;
    baseline.set(k, {
      style: element.getAttribute("style"),
      text: element.children.length === 0 ? element.textContent : null,
      src: element.tagName === "IMG" ? element.getAttribute("src") : null,
      alt: element.tagName === "IMG" ? element.getAttribute("alt") : null,
      title: element.getAttribute("title"),
    });
  }

  function restoreBaseline() {
    for (const [k, state] of baseline.entries()) {
      if (!k.startsWith("path:")) continue;
      let parts;
      try { parts = JSON.parse(k.slice(5)); } catch (_) { continue; }
      const element = resolve(parts);
      if (!element) continue;

      if (state.style === null) element.removeAttribute("style");
      else element.setAttribute("style", state.style);

      if (state.text !== null && element.children.length === 0) {
        element.textContent = state.text;
      }
      if (element.tagName === "IMG") {
        if (state.src === null) element.removeAttribute("src"); else element.setAttribute("src", state.src);
        if (state.alt === null) element.removeAttribute("alt"); else element.setAttribute("alt", state.alt);
      }
      if (state.title === null) element.removeAttribute("title"); else element.setAttribute("title", state.title);
      element.classList.remove("avan-vb-selected");
    }
  }

  function applyStyles(element, styles) {
    for (const [name, value] of Object.entries(styles || {})) {
      if (!STYLE_KEYS.includes(name)) continue;
      element.style[name] = value || "";
    }
  }

  function applyAttrs(element, attrs) {
    if (!attrs || typeof attrs !== "object") return;
    if (element.tagName === "IMG") {
      if (typeof attrs.src === "string") element.setAttribute("src", attrs.src);
      if (typeof attrs.alt === "string") element.setAttribute("alt", attrs.alt);
    }
    if (typeof attrs.title === "string") element.setAttribute("title", attrs.title);
  }

  function ensureInserted(item) {
    let element = document.querySelector(`[data-avan-vb-id="${CSS.escape(item.id)}"]`);
    if (!element) {
      const parent = resolve(item.parent_path);
      if (!parent) return null;
      element = document.createElement(item.tag || "div");
      element.dataset.avanVbInserted = "1";
      element.dataset.avanVbId = item.id;
      parent.appendChild(element);
    }
    if (typeof item.text === "string" && element.tagName !== "IMG") element.textContent = item.text;
    applyAttrs(element, item.attrs);
    applyStyles(element, item.styles);
    return element;
  }

  function applyAll() {
    restoreBaseline();

    for (const item of active.values()) {
      if (item.kind === "insert") continue;
      const element = resolve(item.path);
      if (!element) continue;
      captureBaseline(element, item.path);
      applyStyles(element, item.styles);
      applyAttrs(element, item.attrs);
      if (typeof item.text === "string" && element.children.length === 0) element.textContent = item.text;
      if (item.hidden) element.style.setProperty("display", "none", "important");
    }

    const wanted = new Set(
      [...active.values()].filter(item => item.kind === "insert").map(item => item.id)
    );
    document.querySelectorAll("[data-avan-vb-inserted='1']").forEach(element => {
      if (!wanted.has(element.dataset.avanVbId)) element.remove();
    });
    for (const item of active.values()) {
      if (item.kind === "insert") ensureInserted(item);
    }

    refreshSelection();
  }

  function serializeState() {
    return JSON.stringify([...active.values()]);
  }

  function remember() {
    history = history.slice(0, historyIndex + 1);
    history.push(serializeState());
    historyIndex = history.length - 1;
    if (history.length > 50) {
      history.shift();
      historyIndex--;
    }
    dirty = true;
  }

  function restoreHistory(index) {
    if (index < 0 || index >= history.length) return;
    historyIndex = index;
    active = new Map(
      JSON.parse(history[historyIndex]).map(item => [itemKey(item), item])
    );
    applyAll();
    dirty = true;
  }

  function cookie(name) {
    const escaped = name.replace(/[.$?*|{}()[\]\\/+^]/g, "\\$&");
    const match = document.cookie.match(new RegExp("(?:^|; )" + escaped + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : "";
  }

  function withEditorQuery(enabled) {
    const url = new URL(window.location.href);
    if (enabled) {
      url.searchParams.set("visual_edit", "1");
      url.searchParams.set("visual_preview", "1");
    } else {
      url.searchParams.delete("visual_edit");
      url.searchParams.delete("visual_preview");
    }
    return url.toString();
  }

  function makeId() {
    if (window.crypto?.randomUUID) return "vb-" + crypto.randomUUID();
    return "vb-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  function sameOriginImageUrl(value) {
    try {
      const url = new URL(value, window.location.origin);
      if (url.origin !== window.location.origin) return null;
      return url.pathname + url.search;
    } catch (_) {
      return null;
    }
  }

  const panel = document.createElement("aside");
  panel.className = "avan-visual-panel";
  panel.dataset.avanVisualUi = "1";
  panel.setAttribute("aria-label", "AVAN Visual Studio");
  panel.innerHTML = `
    <div class="avan-vb-top">
      <div><small>AVAN / VISUAL STUDIO</small><strong>ویرایشگر بصری</strong></div>
      <button type="button" data-close aria-label="بستن">×</button>
    </div>

    <div class="avan-vb-device" aria-label="اندازه پیش‌نمایش">
      <button type="button" data-device="desktop" class="is-active">دسکتاپ</button>
      <button type="button" data-device="tablet">تبلت</button>
      <button type="button" data-device="mobile">موبایل</button>
    </div>

    <div class="avan-vb-tools">
      <button type="button" data-add-text>+ متن</button>
      <button type="button" data-upload-image>+ تصویر</button>
      <input type="file" data-image-file accept="image/png,image/jpeg,image/webp,image/gif" hidden>
    </div>

    <div class="avan-vb-section">
      <span>عنصر انتخاب‌شده</span>
      <b data-selected-tag>—</b>
      <label>متن عنصر<textarea data-text rows="3" maxlength="2000"></textarea></label>
      <div class="avan-vb-element-actions">
        <button type="button" data-delete>حذف عنصر</button>
      </div>
    </div>

    <div class="avan-vb-section" data-image-section hidden>
      <span>تصویر</span>
      <label>آدرس تصویر<input data-attr="src" placeholder="/media/..."></label>
      <label>متن جایگزین<input data-attr="alt" maxlength="300"></label>
      <button type="button" data-replace-image>آپلود و جایگزینی تصویر</button>
    </div>

    <div class="avan-vb-section">
      <span>ظاهر و اندازه</span>
      <label>رنگ متن<input data-style="color" placeholder="#171717"></label>
      <label>رنگ پس‌زمینه<input data-style="backgroundColor" placeholder="#FFFFFF"></label>
      <label>اندازه فونت<input data-style="fontSize" placeholder="18px"></label>
      <label>وزن فونت<select data-style="fontWeight"><option value="">پیش‌فرض</option><option>400</option><option>500</option><option>600</option><option>700</option><option>800</option><option>900</option></select></label>
      <label>تراز متن<select data-style="textAlign"><option value="">پیش‌فرض</option><option value="start">شروع</option><option value="center">وسط</option><option value="end">پایان</option><option value="justify">دوطرفه</option></select></label>
      <label>عرض<input data-style="width" placeholder="100% یا 420px"></label>
      <label>ارتفاع<input data-style="height" placeholder="auto یا 240px"></label>
      <label>حداقل ارتفاع<input data-style="minHeight" placeholder="120px"></label>
      <label>حداکثر عرض<input data-style="maxWidth" placeholder="100% یا 600px"></label>
      <label>گردی گوشه<input data-style="borderRadius" placeholder="12px"></label>
      <label>فاصله داخلی<input data-style="padding" placeholder="16px یا 12px 20px"></label>
      <label>فاصله خارجی<input data-style="margin" placeholder="16px یا 0 auto"></label>
      <label>فاصله حروف<input data-style="letterSpacing" placeholder="0px"></label>
      <label>ارتفاع خط<input data-style="lineHeight" placeholder="1.6"></label>
      <label>شفافیت<input data-style="opacity" placeholder="1"></label>
      <label>حالت برش تصویر<select data-style="objectFit"><option value="">پیش‌فرض</option><option value="cover">cover</option><option value="contain">contain</option><option value="fill">fill</option></select></label>
    </div>

    <div class="avan-vb-status" data-status>برای شروع روی یک عنصر کلیک کن.</div>

    <div class="avan-vb-actions">
      <button type="button" data-undo>بازگشت</button>
      <button type="button" data-redo>تکرار</button>
    </div>
    <div class="avan-vb-actions">
      <button type="button" data-save>ذخیره پیش‌نویس</button>
      <button type="button" data-publish>انتشار</button>
    </div>`;
  document.body.appendChild(panel);

  const status = panel.querySelector("[data-status]");
  const imageSection = panel.querySelector("[data-image-section]");
  const fileInput = panel.querySelector("[data-image-file]");

  const banner = document.createElement("div");
  banner.className = "avan-vb-banner";
  banner.dataset.avanVisualUi = "1";
  banner.innerHTML = `<span>حالت طراحی فعال است؛ روی هر عنصر کلیک کن.</span><button type="button" data-exit>خروج از طراحی</button>`;
  document.body.appendChild(banner);

  function setMode(enabled) {
    editMode = enabled;
    document.body.classList.toggle("avan-vb-mode", enabled);
    panel.classList.toggle("is-open", enabled);
    banner.classList.toggle("is-open", enabled);
    launches.forEach(button => {
      button.textContent = enabled ? "پایان طراحی" : (button.dataset.label || "طراحی");
    });
    if (!enabled && selected) {
      selected.classList.remove("avan-vb-selected");
      selected = null;
      selectedKey = null;
    }
  }

  function exitMode() {
    if (dirty && !window.confirm("تغییرات ذخیره‌نشده باقی مانده‌اند. بدون ذخیره خارج می‌شوی؟")) return;
    window.location.assign(withEditorQuery(false));
  }

  function currentItem() {
    if (!selectedKey) return null;
    return active.get(selectedKey) || null;
  }

  function ensureItemForElement(element) {
    if (element.dataset.avanVbInserted === "1") {
      const k = "insert:" + element.dataset.avanVbId;
      return [k, active.get(k) || null];
    }
    const path = nodePath(element);
    if (!path) return [null, null];
    captureBaseline(element, path);
    const k = pathKey(path);
    const item = active.get(k) || { kind: "style", path, styles: {}, attrs: {}, text: null, hidden: false };
    return [k, item];
  }

  function fieldValue(element, prop, item) {
    if (Object.prototype.hasOwnProperty.call(item?.styles || {}, prop)) return item.styles[prop] || "";
    const computed = getComputedStyle(element);
    return computed[prop] || "";
  }

  function selectElement(element) {
    if (!editMode || !element || panel.contains(element) ||
        element.closest("[data-avan-visual-ui]") ||
        ["BODY", "HTML", "SCRIPT", "STYLE", "LINK", "META"].includes(element.tagName)) return;

    if (selected) selected.classList.remove("avan-vb-selected");
    selected = element;
    element.classList.add("avan-vb-selected");

    const [k, item] = ensureItemForElement(element);
    if (!k) return;
    selectedKey = k;

    panel.querySelectorAll("[data-style]").forEach(input => {
      input.value = fieldValue(element, input.dataset.style, item);
    });

    const textInput = panel.querySelector("[data-text]");
    const textEditable = element.tagName !== "IMG" && element.children.length === 0;
    textInput.disabled = !textEditable;
    textInput.value = textEditable ? (item?.text ?? element.textContent.trim().slice(0, 2000)) : "";

    const isImage = element.tagName === "IMG";
    imageSection.hidden = !isImage;
    panel.querySelector("[data-attr='src']").value = isImage ? (item?.attrs?.src ?? element.getAttribute("src") ?? "") : "";
    panel.querySelector("[data-attr='alt']").value = isImage ? (item?.attrs?.alt ?? element.getAttribute("alt") ?? "") : "";

    panel.querySelector("[data-selected-tag]").textContent =
      element.dataset.avanVbInserted === "1"
        ? `${element.tagName.toLowerCase()} / جدید`
        : element.tagName.toLowerCase();

    status.textContent = isImage
      ? "می‌توانی تصویر را جایگزین و اندازه‌اش را تغییر بدهی."
      : textEditable
        ? "متن و ظاهر این عنصر قابل ویرایش است."
        : "ظاهر و اندازه این عنصر قابل ویرایش است.";
  }

  function refreshSelection() {
    if (!selectedKey) return;
    if (selectedKey.startsWith("insert:")) {
      const id = selectedKey.slice(7);
      const element = document.querySelector(`[data-avan-vb-id="${CSS.escape(id)}"]`);
      if (element) {
        selected = element;
        element.classList.add("avan-vb-selected");
      }
      return;
    }
    try {
      const path = JSON.parse(selectedKey.slice(5));
      const element = resolve(path);
      if (element) {
        selected = element;
        element.classList.add("avan-vb-selected");
      }
    } catch (_) {}
  }

  function updateStyle(input) {
    if (!selected) return;
    const [k, item] = ensureItemForElement(selected);
    if (!k || !item) return;
    item.styles = item.styles || {};
    item.styles[input.dataset.style] = input.value.trim();
    active.set(k, item);
    applyStyles(selected, { [input.dataset.style]: item.styles[input.dataset.style] });
    remember();
    status.textContent = "تغییر زنده اعمال شد.";
  }

  function updateAttr(input) {
    if (!selected || selected.tagName !== "IMG") return;
    const [k, item] = ensureItemForElement(selected);
    if (!k || !item) return;
    item.attrs = item.attrs || {};
    const attr = input.dataset.attr;
    let value = input.value.trim();
    if (attr === "src") {
      const safe = sameOriginImageUrl(value);
      if (!safe) {
        status.textContent = "برای تصویر فقط آدرس همین سایت مجاز است.";
        return;
      }
      value = safe;
    }
    item.attrs[attr] = value;
    active.set(k, item);
    applyAttrs(selected, item.attrs);
    remember();
  }

  function insertParent() {
    if (selected && ["SECTION", "DIV", "MAIN", "ARTICLE", "ASIDE", "HEADER", "FOOTER", "NAV"].includes(selected.tagName)) {
      return selected;
    }
    if (selected?.parentElement && selected.parentElement !== document.body) return selected.parentElement;
    return document.querySelector("main") || document.body;
  }

  function addText() {
    const parent = insertParent();
    const parentPath = nodePath(parent);
    if (!parentPath) {
      status.textContent = "محل مناسبی برای افزودن متن پیدا نشد.";
      return;
    }
    const item = {
      kind: "insert",
      id: makeId(),
      parent_path: parentPath,
      tag: "p",
      text: "متن جدید",
      attrs: {},
      styles: { fontSize: "18px", lineHeight: "1.7" }
    };
    active.set(itemKey(item), item);
    ensureInserted(item);
    remember();
    const element = document.querySelector(`[data-avan-vb-id="${CSS.escape(item.id)}"]`);
    if (element) selectElement(element);
    status.textContent = "متن جدید اضافه شد؛ حالا متن و ظاهرش را تغییر بده.";
  }

  async function uploadImage(file, replaceSelected = false) {
    if (!file) return;
    if (busy) return;
    busy = true;
    status.textContent = "در حال آپلود تصویر…";
    try {
      const csrf = document.querySelector("#avan-csrf input[name=csrfmiddlewaretoken]")?.value || cookie("csrftoken");
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(UPLOAD_API, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest" },
        body: form
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "آپلود تصویر انجام نشد.");

      if (replaceSelected && selected?.tagName === "IMG") {
        const [k, item] = ensureItemForElement(selected);
        item.attrs = item.attrs || {};
        item.attrs.src = result.url;
        active.set(k, item);
        selected.setAttribute("src", result.url);
        panel.querySelector("[data-attr='src']").value = result.url;
        remember();
        status.textContent = "تصویر جایگزین شد.";
        return;
      }

      const parent = insertParent();
      const parentPath = nodePath(parent);
      if (!parentPath) throw new Error("محل مناسبی برای افزودن تصویر پیدا نشد.");
      const item = {
        kind: "insert",
        id: makeId(),
        parent_path: parentPath,
        tag: "img",
        text: null,
        attrs: { src: result.url, alt: "" },
        styles: { maxWidth: "100%", height: "auto", objectFit: "cover" }
      };
      active.set(itemKey(item), item);
      ensureInserted(item);
      remember();
      const element = document.querySelector(`[data-avan-vb-id="${CSS.escape(item.id)}"]`);
      if (element) selectElement(element);
      status.textContent = "تصویر جدید اضافه شد.";
    } catch (error) {
      status.textContent = error.message || "خطا در آپلود تصویر.";
    } finally {
      busy = false;
      fileInput.value = "";
    }
  }

  function deleteSelected() {
    if (!selected || !selectedKey) return;
    if (!window.confirm("این عنصر از صفحه حذف شود؟")) return;

    if (selectedKey.startsWith("insert:")) {
      active.delete(selectedKey);
      selected.remove();
    } else {
      const [k, item] = ensureItemForElement(selected);
      item.hidden = true;
      active.set(k, item);
      selected.style.setProperty("display", "none", "important");
    }

    selected = null;
    selectedKey = null;
    panel.querySelector("[data-selected-tag]").textContent = "—";
    imageSection.hidden = true;
    remember();
    status.textContent = "عنصر حذف شد. برای برگرداندن از «بازگشت» استفاده کن.";
  }

  launches.forEach(button => {
    button.dataset.label = button.textContent.trim() || "طراحی";
    button.addEventListener("click", () => {
      if (!editMode) {
        if (new URLSearchParams(window.location.search).get("visual_edit") !== "1") {
          window.location.assign(withEditorQuery(true));
          return;
        }
        setMode(true);
      } else {
        exitMode();
      }
    });
  });

  panel.querySelector("[data-close]").addEventListener("click", exitMode);
  banner.querySelector("[data-exit]").addEventListener("click", exitMode);

  document.addEventListener("click", event => {
    if (!editMode || panel.contains(event.target) || event.target.closest("[data-avan-visual-ui]")) return;
    const element = event.target.closest("body *");
    if (!element) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    selectElement(element);
  }, true);

  // Prevent accidental form submission while visually editing account/support pages.
  document.addEventListener("submit", event => {
    if (!editMode) return;
    event.preventDefault();
    event.stopPropagation();
    status.textContent = "ارسال فرم در حالت طراحی غیرفعال است.";
  }, true);

  panel.querySelectorAll("[data-style]").forEach(input => {
    input.addEventListener("input", () => updateStyle(input));
    input.addEventListener("change", () => updateStyle(input));
  });

  panel.querySelectorAll("[data-attr]").forEach(input => {
    input.addEventListener("change", () => updateAttr(input));
  });

  panel.querySelector("[data-text]").addEventListener("input", event => {
    if (!selected || selected.tagName === "IMG" || selected.children.length) return;
    const [k, item] = ensureItemForElement(selected);
    if (!k || !item) return;
    item.text = event.target.value.slice(0, 2000);
    active.set(k, item);
    selected.textContent = item.text;
    remember();
  });

  panel.querySelector("[data-add-text]").addEventListener("click", addText);
  panel.querySelector("[data-upload-image]").addEventListener("click", () => {
    fileInput.dataset.replace = "0";
    fileInput.click();
  });
  panel.querySelector("[data-replace-image]").addEventListener("click", () => {
    fileInput.dataset.replace = "1";
    fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    uploadImage(file, fileInput.dataset.replace === "1");
  });
  panel.querySelector("[data-delete]").addEventListener("click", deleteSelected);

  panel.querySelectorAll("[data-device]").forEach(button => {
    button.addEventListener("click", () => {
      panel.querySelectorAll("[data-device]").forEach(item => item.classList.toggle("is-active", item === button));
      document.documentElement.dataset.avanPreviewDevice = button.dataset.device;
      if (window.frameElement) {
        const widths = { desktop: "100%", tablet: "820px", mobile: "390px" };
        window.frameElement.style.width = widths[button.dataset.device];
        window.frameElement.style.maxWidth = "100%";
        window.frameElement.style.marginInline = "auto";
      }
      status.textContent = "پیش‌نمایش روی حالت " + button.textContent + " تنظیم شد.";
    });
  });

  panel.querySelector("[data-undo]").addEventListener("click", () => {
    if (historyIndex <= 0) return;
    restoreHistory(historyIndex - 1);
  });
  panel.querySelector("[data-redo]").addEventListener("click", () => {
    if (historyIndex >= history.length - 1) return;
    restoreHistory(historyIndex + 1);
  });

  async function persist(action) {
    if (busy) return;
    busy = true;
    status.textContent = "در حال ذخیره…";
    try {
      const csrf = document.querySelector("#avan-csrf input[name=csrfmiddlewaretoken]")?.value || cookie("csrftoken");
      const response = await fetch(API, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
          "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({ path: pagePath, action, elements: [...active.values()] })
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "ذخیره انجام نشد.");
      dirty = false;
      status.textContent = action === "publish"
        ? `تغییرات منتشر شد (${result.elements_saved || 0} عنصر).`
        : `پیش‌نویس ذخیره شد (${result.elements_saved || 0} عنصر).`;
      if (action === "publish") window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      status.textContent = error.message || "خطا در ذخیره‌سازی.";
    } finally {
      busy = false;
    }
  }

  panel.querySelector("[data-save]").addEventListener("click", () => persist("save"));
  panel.querySelector("[data-publish]").addEventListener("click", () => {
    if (window.confirm("تغییرات این صفحه برای همه بازدیدکنندگان منتشر شود؟")) persist("publish");
  });

  (Array.isArray(pageData.elements) ? pageData.elements : []).forEach(item => {
    if (!item || typeof item !== "object") return;
    if (!item.kind) item.kind = "style";
    active.set(itemKey(item), item);
  });

  applyAll();
  history = [serializeState()];
  historyIndex = 0;
  dirty = false;

  if (new URLSearchParams(window.location.search).get("visual_edit") === "1") setMode(true);
})();