/**
 * Assistente IA no formulário de produto.
 * Upload PDF → antivírus no servidor → preview → só aplica ao form após aprovação.
 * Inclui painel HITL de peças e sync de selected_part_codes no save.
 */
(function () {
  const root = document.getElementById("product-ai-assist");
  if (!root) return;

  const extractUrl = root.dataset.extractUrl;
  const discardTemplate =
    root.dataset.discardUrlTemplate ||
    "/dashboard/produtos/ia/extrair-manual/__ID__/descartar/";
  const csrf = root.dataset.csrf;
  const fileInput = document.getElementById("product-ai-pdf");
  const analyzeBtn = document.getElementById("product-ai-analyze");
  const statusEl = document.getElementById("product-ai-status");
  const agentEl = document.getElementById("product-ai-agent");
  const titleEl = document.getElementById("product-ai-agent-title");
  const msgEl = document.getElementById("product-ai-agent-msg");
  const badgesEl = document.getElementById("product-ai-badges");
  const highlightsEl = document.getElementById("product-ai-highlights");
  const jsonEl = document.getElementById("product-ai-json");
  const partsWrap = document.getElementById("product-ai-parts");
  const partsBody = document.getElementById("product-ai-parts-body");
  const partsAllBtn = document.getElementById("product-ai-parts-all");
  const partsNoneBtn = document.getElementById("product-ai-parts-none");
  const modelPickerWrap = document.getElementById("product-ai-model-picker");
  const modelSelect = document.getElementById("product-ai-model-select");
  const sectionsEl = document.getElementById("product-ai-sections");
  const approveBtn = document.getElementById("product-ai-approve");
  const discardBtn = document.getElementById("product-ai-discard");
  const extractionField = document.getElementById("id_extraction_id");
  const selectedPartsField = document.getElementById("id_selected_part_codes");
  const loadingModalEl = document.getElementById("product-ai-loading-modal");
  const loadingStepEl = document.getElementById("product-ai-loading-step");
  const mainForm = document.getElementById("product-main-form");

  let current = null;
  let loadingModal = null;
  let modelResolvedByHuman = false;

  function getLoadingModal() {
    if (loadingModal) return loadingModal;
    if (!loadingModalEl || !window.bootstrap || !window.bootstrap.Modal) return null;
    loadingModal = window.bootstrap.Modal.getOrCreateInstance(loadingModalEl);
    return loadingModal;
  }

  function showLoading(stepText) {
    if (loadingStepEl && stepText) loadingStepEl.textContent = stepText;
    const modal = getLoadingModal();
    if (modal) modal.show();
  }

  function hideLoading() {
    const modal = getLoadingModal();
    if (modal) modal.hide();
  }

  function setStatus(text, kind) {
    statusEl.hidden = !text;
    statusEl.textContent = text || "";
    statusEl.className = "small mt-3";
    if (kind === "error") statusEl.classList.add("text-danger");
    else if (kind === "ok") statusEl.classList.add("text-success");
    else statusEl.classList.add("text-secondary");
  }

  function hideAgent() {
    agentEl.hidden = true;
    current = null;
    modelResolvedByHuman = false;
    if (extractionField) extractionField.value = "";
    if (selectedPartsField) selectedPartsField.value = "";
    if (partsWrap) partsWrap.hidden = true;
    if (partsBody) partsBody.innerHTML = "";
    if (modelPickerWrap) modelPickerWrap.hidden = true;
    if (modelSelect) modelSelect.innerHTML = "";
    if (sectionsEl) {
      sectionsEl.hidden = true;
      sectionsEl.innerHTML = "";
    }
  }

  function badge(text, cls) {
    const span = document.createElement("span");
    span.className = "badge " + (cls || "text-bg-light border");
    span.textContent = text;
    return span;
  }

  function row(dt, dd) {
    const dtEl = document.createElement("dt");
    dtEl.className = "col-sm-3";
    dtEl.textContent = dt;
    const ddEl = document.createElement("dd");
    ddEl.className = "col-sm-9 font-monospace mb-1";
    ddEl.textContent = dd == null || dd === "" ? "—" : String(dd);
    highlightsEl.appendChild(dtEl);
    highlightsEl.appendChild(ddEl);
  }

  function displayConfidence() {
    if (!current) return 0.5;
    let conf = Number(current.confidence);
    if (Number.isNaN(conf)) conf = 0.5;
    if (modelResolvedByHuman) conf = Math.min(0.95, conf + 0.18);
    return conf;
  }

  function lowConfidenceFields() {
    const summary = (current && current.summary) || {};
    const sug = (current && current.form_suggestions) || {};
    let fields = (summary.low_confidence_fields || sug.low_confidence_fields || []).slice();
    if (modelResolvedByHuman) {
      fields = fields.filter(function (f) {
        return String(f).toLowerCase() !== "model_code";
      });
    }
    return fields;
  }

  function refreshTitleAndBadges() {
    if (!current) return;
    const ex = current.extracted || {};
    const conf = displayConfidence();
    titleEl.textContent =
      (ex.name || ex.sku_suggestion || current.filename || "Proposta") +
      " · confiança " +
      (conf * 100).toFixed(0) +
      "%";
    badgesEl.innerHTML = "";
    if (current.scan_status) {
      badgesEl.appendChild(
        badge(
          "AV: " + current.scan_status,
          current.scan_status === "clean" || current.scan_status === "skipped"
            ? "text-bg-success"
            : "text-bg-warning"
        )
      );
    }
    const summary = current.summary || {};
    if (summary.sellable_parts) {
      badgesEl.appendChild(badge(summary.sellable_parts + " peças vendáveis", "text-bg-success"));
    }
    if (summary.composition_only) {
      badgesEl.appendChild(badge(summary.composition_only + " só composição", "text-bg-secondary"));
    }
    if (summary.document_conflicts) {
      badgesEl.appendChild(
        badge(summary.document_conflicts + " divergências", "text-bg-warning")
      );
    }
    (summary.source_doc_types || []).forEach(function (t) {
      badgesEl.appendChild(badge(t));
    });
    if (modelResolvedByHuman) {
      badgesEl.appendChild(badge("modelo confirmado", "text-bg-success"));
    }
    const low = lowConfidenceFields();
    if (low.length) {
      badgesEl.appendChild(badge("baixa confiança: " + low.join(", "), "text-bg-warning"));
    }
  }

  function renderSections(sections) {
    if (!sectionsEl) return;
    sectionsEl.innerHTML = "";
    if (!sections) {
      sectionsEl.hidden = true;
      return;
    }
    const blocks = [
      { key: "model_variants", title: "Variantes de modelo" },
      { key: "characteristics", title: "Características" },
      { key: "components", title: "Componentes" },
      { key: "safety_warnings", title: "Avisos de segurança" },
      { key: "key_usage_steps", title: "Como utilizar" },
      { key: "installation_requirements", title: "Instalação / manuseio" },
      { key: "warranty", title: "Garantia" },
      { key: "certifications", title: "Certificações" },
    ];
    let any = false;
    blocks.forEach(function (block) {
      const items = sections[block.key] || [];
      if (!items.length) return;
      any = true;
      const wrap = document.createElement("div");
      wrap.className = "mb-3";
      const h = document.createElement("p");
      h.className = "font-label-caps text-secondary mb-1";
      h.textContent = block.title;
      const ul = document.createElement("ul");
      ul.className = "small mb-0 ps-3";
      items.forEach(function (item) {
        const li = document.createElement("li");
        li.textContent = item;
        ul.appendChild(li);
      });
      wrap.appendChild(h);
      wrap.appendChild(ul);
      sectionsEl.appendChild(wrap);
    });
    sectionsEl.hidden = !any;
  }

  function skuFromBrandModel(brand, model) {
    const b = String(brand || "XX")
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, "")
      .slice(0, 8);
    const m = String(model || "")
      .toUpperCase()
      .replace(/\s+/g, "-")
      .replace(/[^A-Z0-9\-]/g, "");
    return (b + (m ? "-" + m : "")).replace(/-+/g, "-").replace(/^-|-$/g, "") || m;
  }

  function applySelectedModel(modelCode) {
    if (!current || !modelCode) return;
    modelResolvedByHuman = true;
    const sug = current.form_suggestions || (current.form_suggestions = {});
    const ex = current.extracted || {};
    const options = current.model_options || [];
    const match = options.find(function (o) {
      return (o.code || o) === modelCode || o === modelCode;
    });
    const brand = sug.brand_name || ex.brand || ex.manufacturer || "";
    sug.model_code = modelCode;
    if (match && match.sku) {
      sug.sku = match.sku;
    } else {
      sug.sku = skuFromBrandModel(brand, modelCode);
    }
    if (match && match.equipment_model_id) {
      sug.equipment_model = match.equipment_model_id;
    }
    const low = (sug.low_confidence_fields || []).filter(function (f) {
      return String(f).toLowerCase() !== "model_code";
    });
    sug.low_confidence_fields = low;
    if (current.summary) {
      current.summary.low_confidence_fields = low;
    }
    if (ex.model_code !== undefined) ex.model_code = modelCode;
    if (ex.sku_suggestion !== undefined) ex.sku_suggestion = sug.sku;
    refreshTitleAndBadges();
    highlightsEl.innerHTML = "";
    row("Marca", ex.brand || ex.manufacturer);
    row("Modelo", modelCode);
    row("SKU sugerido", sug.sku);
    row("Categoria", ex.category || ex.category_hint);
    row("Descrição", ex.description);
    row("Voltagem", ex.voltage);
    row("Potência (W)", ex.power_w);
    row("Peças / acessórios", (ex.spare_parts || []).length + (ex.accessories || []).length);
  }

  function renderModelPicker(options) {
    if (!modelPickerWrap || !modelSelect) return;
    modelSelect.innerHTML = "";
    const normalized = (options || []).map(function (o) {
      if (typeof o === "string") return { code: o, label: o };
      return o;
    });
    if (normalized.length < 2) {
      modelPickerWrap.hidden = true;
      return;
    }
    modelPickerWrap.hidden = false;
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecione o modelo…";
    modelSelect.appendChild(placeholder);
    normalized.forEach(function (item) {
      const opt = document.createElement("option");
      opt.value = item.code;
      opt.textContent = item.label || item.code;
      modelSelect.appendChild(opt);
    });
  }

  function syncSelectedPartsField() {
    if (!selectedPartsField || !partsBody) return;
    const codes = [];
    partsBody.querySelectorAll('input[data-part-code]:checked').forEach(function (el) {
      const code = el.getAttribute("data-part-code");
      if (code) codes.push(code);
    });
    selectedPartsField.value = codes.join(",");
  }

  function renderParts(parts) {
    if (!partsWrap || !partsBody) return;
    partsBody.innerHTML = "";
    if (!parts || !parts.length) {
      partsWrap.hidden = true;
      syncSelectedPartsField();
      return;
    }
    partsWrap.hidden = false;
    parts.forEach(function (part) {
      const tr = document.createElement("tr");
      const sellable = Boolean(part.sellable_separately && part.code);
      const tdCheck = document.createElement("td");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.className = "form-check-input";
      cb.disabled = !sellable;
      cb.checked = Boolean(part.selected && sellable);
      if (sellable) {
        cb.setAttribute("data-part-code", part.code);
        cb.addEventListener("change", syncSelectedPartsField);
      }
      tdCheck.appendChild(cb);

      const tdCode = document.createElement("td");
      tdCode.className = "font-monospace small";
      tdCode.textContent = part.code || "—";

      const tdName = document.createElement("td");
      tdName.textContent = part.name || "—";
      if (part.ref_number) {
        const ref = document.createElement("span");
        ref.className = "text-secondary small d-block";
        ref.textContent = "Ref. " + part.ref_number;
        tdName.appendChild(ref);
      }

      const tdSku = document.createElement("td");
      tdSku.className = "font-monospace small";
      tdSku.textContent = part.sku_suggestion || "—";

      const tdKind = document.createElement("td");
      const kindBadge = document.createElement("span");
      kindBadge.className =
        "badge " + (sellable ? "text-bg-success" : "text-bg-secondary");
      kindBadge.textContent = sellable
        ? part.kind === "accessory"
          ? "Acessório"
          : "Vendável"
        : "Só composição";
      tdKind.appendChild(kindBadge);

      tr.appendChild(tdCheck);
      tr.appendChild(tdCode);
      tr.appendChild(tdName);
      tr.appendChild(tdSku);
      tr.appendChild(tdKind);
      partsBody.appendChild(tr);
    });
    syncSelectedPartsField();
  }

  function showAgent(payload) {
    current = payload;
    modelResolvedByHuman = false;
    agentEl.hidden = false;
    const ex = payload.extracted || {};
    msgEl.textContent = payload.message || "";
    refreshTitleAndBadges();

    highlightsEl.innerHTML = "";
    row("Marca", ex.brand || ex.manufacturer);
    row("Modelo", ex.model_code);
    row("SKU sugerido", ex.sku_suggestion);
    row("Categoria", ex.category || ex.category_hint);
    row("Descrição", ex.description);
    row("Voltagem", ex.voltage);
    row("Potência (W)", ex.power_w);
    row("Peças / acessórios", (ex.spare_parts || []).length + (ex.accessories || []).length);
    const conflicts = ex.document_conflicts || [];
    if (conflicts.length) {
      row(
        "Divergências",
        conflicts
          .map(function (c) {
            return (c.field || "?") + ": " + (c.values || []).join(" | ");
          })
          .join("; ")
      );
    }

    jsonEl.textContent = JSON.stringify(ex, null, 2);
    renderParts(payload.parts_for_review || []);
    renderSections(payload.proposal_sections || {});
    renderModelPicker(payload.model_options || []);
  }

  function setField(name, value, label) {
    if (value === null || value === undefined || value === "") return;
    const el = document.getElementById("id_" + name) || document.querySelector('[name="' + name + '"]');
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = Boolean(value);
      return;
    }
    if (el.tagName === "SELECT") {
      const strVal = String(value);
      let opt = Array.prototype.find.call(el.options, function (o) {
        return o.value === strVal;
      });
      if (!opt) {
        opt = document.createElement("option");
        opt.value = strVal;
        opt.textContent = label || strVal;
        el.appendChild(opt);
      } else if (label) {
        opt.textContent = label;
      }
    }
    el.value = String(value);
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function applySuggestions(sug) {
    if (!sug) return;
    setField("sku", sug.sku);
    setField("brand_ref", sug.brand_ref, sug.brand_name);
    setField(
      "equipment_model",
      sug.equipment_model,
      sug.brand_name && sug.model_code
        ? sug.brand_name + " " + sug.model_code
        : sug.model_code
    );
    setField("name", sug.name);
    setField("description", sug.description);
    setField("voltage", sug.voltage);
    setField("product_kind", sug.product_kind);
    setField("status", sug.status || "draft");
    setField("category", sug.category, sug.category_name);
    setField("power_w", sug.power_w);
    setField("weight_kg", sug.weight_kg);
    setField("dim_height_cm", sug.dim_height_cm);
    setField("dim_width_cm", sug.dim_width_cm);
    setField("dim_depth_cm", sug.dim_depth_cm);
    setField("diameter_cm", sug.diameter_cm);
    setField("blade_count", sug.blade_count);
    setField("material", sug.material);
    setField("color", sug.color);
    setField("rpm", sug.rpm);
    setField("mounting", sug.mounting);
    setField("bearing_type", sug.bearing_type);
    setField("remote_included", sug.remote_included);
    setField("specs_extra", sug.specs_extra);
  }

  analyzeBtn.addEventListener("click", async function () {
    const file = fileInput && fileInput.files && fileInput.files[0];
    if (!file) {
      setStatus("Selecione um arquivo PDF.", "error");
      return;
    }
    if (!/\.pdf$/i.test(file.name)) {
      setStatus("Apenas arquivos .pdf são aceitos.", "error");
      return;
    }

    analyzeBtn.disabled = true;
    hideAgent();
    setStatus("Enviando PDF, verificando antivírus e extraindo com a IA…");
    showLoading("Enviando PDF, verificando antivírus e extraindo com a IA…");

    const body = new FormData();
    body.append("manual", file);

    try {
      const res = await fetch(extractUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrf, Accept: "application/json" },
        body: body,
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setStatus(data.error || "Falha na análise.", "error");
        return;
      }
      setStatus(
        "Análise concluída. Revise a proposta e as peças abaixo — nada foi aplicado ainda.",
        "ok"
      );
      showAgent(data);
    } catch (err) {
      setStatus("Erro de rede ao enviar o PDF.", "error");
    } finally {
      hideLoading();
      analyzeBtn.disabled = false;
    }
  });

  if (modelSelect) {
    modelSelect.addEventListener("change", function () {
      if (!modelSelect.value) return;
      applySelectedModel(modelSelect.value);
    });
  }

  if (partsAllBtn) {
    partsAllBtn.addEventListener("click", function () {
      if (!partsBody) return;
      partsBody.querySelectorAll("input[data-part-code]").forEach(function (el) {
        el.checked = true;
      });
      syncSelectedPartsField();
    });
  }
  if (partsNoneBtn) {
    partsNoneBtn.addEventListener("click", function () {
      if (!partsBody) return;
      partsBody.querySelectorAll("input[data-part-code]").forEach(function (el) {
        el.checked = false;
      });
      syncSelectedPartsField();
    });
  }

  approveBtn.addEventListener("click", function () {
    if (!current) return;
    if (modelSelect && modelSelect.value) {
      applySelectedModel(modelSelect.value);
    }
    applySuggestions(current.form_suggestions || {});
    if (extractionField) extractionField.value = String(current.extraction_id || "");
    syncSelectedPartsField();
    setStatus(
      "Proposta aprovada e copiada para o formulário. Revise os campos e as peças marcadas; ao Salvar, o manual PDF fica vinculado para download e as peças selecionadas são cadastradas.",
      "ok"
    );
    const form = document.getElementById("product-main-form");
    if (form) form.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  if (mainForm) {
    mainForm.addEventListener("submit", function () {
      syncSelectedPartsField();
    });
  }

  discardBtn.addEventListener("click", async function () {
    if (!current || !current.extraction_id) {
      hideAgent();
      setStatus("Proposta descartada.", "ok");
      return;
    }
    discardBtn.disabled = true;
    try {
      const discardUrl = discardTemplate.replace("__ID__", String(current.extraction_id));
      const body = new FormData();
      const res = await fetch(discardUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrf, Accept: "application/json" },
        body: body,
      });
      const data = await res.json().catch(function () {
        return {};
      });
      if (!res.ok || data.ok === false) {
        setStatus(data.error || "Não foi possível descartar.", "error");
        return;
      }
      hideAgent();
      if (fileInput) fileInput.value = "";
      setStatus("Proposta descartada. Nenhum dado foi aplicado.", "ok");
    } catch (err) {
      setStatus("Erro ao descartar a proposta.", "error");
    } finally {
      discardBtn.disabled = false;
    }
  });
})();
