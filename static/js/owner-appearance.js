(() => {
  "use strict";

  const editor = document.querySelector("[data-appearance-editor]");
  if (!editor) return;

  const form = editor.querySelector("[data-appearance-form]");
  const preview = editor.querySelector("[data-appearance-preview]");
  if (!form || !preview) return;

  const isFa = document.documentElement.lang.toLowerCase().startsWith("fa");
  const ids = [
    "id_primary_color",
    "id_light_background",
    "id_light_surface",
    "id_dark_background",
    "id_dark_surface",
    "id_base_font_size",
    "id_persian_font_size",
    "id_content_width",
    "id_page_gutter",
    "id_header_height",
    "id_section_spacing",
    "id_card_radius",
    "id_button_radius",
    "id_card_shadow",
  ];

  const fields = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
  const initial = Object.fromEntries(ids.map((id) => {
    const field = fields[id];
    return [id, field?.type === "checkbox" ? Boolean(field.checked) : field?.value];
  }));

  const val = (id, fallback) => fields[id]?.value || fallback;
  const checked = (id) => Boolean(fields[id]?.checked);

  function applyPreview() {
    const dark = preview.classList.contains("is-dark");
    const bg = dark ? val("id_dark_background", "#0D0D0F") : val("id_light_background", "#FFFFFF");
    const surface = dark ? val("id_dark_surface", "#17171A") : val("id_light_surface", "#F7F7F7");
    const font = isFa ? val("id_persian_font_size", "18") : val("id_base_font_size", "17");

    preview.style.setProperty("--preview-accent", val("id_primary_color", "#D50000"));
    preview.style.setProperty("--preview-bg", bg);
    preview.style.setProperty("--preview-surface", surface);
    preview.style.setProperty("--preview-font", `${font}px`);
    preview.style.setProperty("--preview-radius", `${val("id_card_radius", "12")}px`);
    preview.style.setProperty("--preview-btn-radius", `${val("id_button_radius", "8")}px`);
    preview.style.setProperty("--preview-gutter", `${Math.min(Number(val("id_page_gutter", "32")), 48)}px`);
    preview.style.setProperty("--preview-header", `${val("id_header_height", "76")}px`);
    preview.style.setProperty("--preview-shadow", checked("id_card_shadow") ? "0 14px 34px rgba(17,17,17,.075)" : "none");
    preview.style.background = bg;

    document.querySelectorAll("[data-color-output]").forEach((node) => {
      const field = fields[node.dataset.colorOutput];
      if (field) node.textContent = field.value.toUpperCase();
    });
  }

  function setValues(values) {
    Object.entries(values).forEach(([id, value]) => {
      const field = fields[id];
      if (!field) return;
      if (field.type === "checkbox") field.checked = Boolean(value);
      else field.value = String(value);
    });
    applyPreview();
  }

  form.addEventListener("input", applyPreview);
  form.addEventListener("change", applyPreview);

  document.querySelectorAll("[data-preview-theme]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-preview-theme]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      preview.classList.toggle("is-dark", button.dataset.previewTheme === "dark");
      applyPreview();
    });
  });

  document.querySelectorAll("[data-preview-device]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-preview-device]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      preview.classList.toggle("is-mobile", button.dataset.previewDevice === "mobile");
    });
  });

  document.querySelector("[data-appearance-revert]")?.addEventListener("click", () => setValues(initial));

  const presets = {
    clean: {
      id_primary_color: "#D50000",
      id_light_background: "#FFFFFF",
      id_light_surface: "#F7F7F7",
      id_dark_background: "#0D0D0F",
      id_dark_surface: "#17171A",
      id_base_font_size: 17,
      id_persian_font_size: 18,
      id_content_width: 1440,
      id_page_gutter: 32,
      id_header_height: 76,
      id_section_spacing: 72,
      id_card_radius: 10,
      id_button_radius: 7,
      id_card_shadow: false,
    },
    soft: {
      id_primary_color: "#D50000",
      id_light_background: "#FCFCFB",
      id_light_surface: "#F4F4F1",
      id_dark_background: "#0D0D0F",
      id_dark_surface: "#18181B",
      id_base_font_size: 17,
      id_persian_font_size: 19,
      id_content_width: 1480,
      id_page_gutter: 38,
      id_header_height: 78,
      id_section_spacing: 80,
      id_card_radius: 18,
      id_button_radius: 12,
      id_card_shadow: true,
    },
    bold: {
      id_primary_color: "#C90000",
      id_light_background: "#FFFFFF",
      id_light_surface: "#F2F2F2",
      id_dark_background: "#09090A",
      id_dark_surface: "#151517",
      id_base_font_size: 18,
      id_persian_font_size: 20,
      id_content_width: 1560,
      id_page_gutter: 44,
      id_header_height: 82,
      id_section_spacing: 92,
      id_card_radius: 6,
      id_button_radius: 4,
      id_card_shadow: true,
    },
  };

  document.querySelectorAll("[data-appearance-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = presets[button.dataset.appearancePreset];
      if (preset) setValues(preset);
    });
  });

  applyPreview();
})();
