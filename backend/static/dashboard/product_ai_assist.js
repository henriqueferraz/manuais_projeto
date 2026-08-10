/**
 * Assistente IA no formulário de produto.
 * Upload PDF → antivírus no servidor → preview → só aplica ao form após aprovação.
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
  const approveBtn = document.getElementById("product-ai-approve");
  const discardBtn = document.getElementById("product-ai-discard");
  const extractionField = document.getElementById("id_extraction_id");

  let current = null;

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
    if (extractionField) extractionField.value = "";
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

  function showAgent(payload) {
    current = payload;
    agentEl.hidden = false;
    const ex = payload.extracted || {};
    titleEl.textContent =
      (ex.name || ex.sku_suggestion || payload.filename || "Proposta") +
      (payload.confidence != null ? ` · confiança ${(Number(payload.confidence) * 100).toFixed(0)}%` : "");
    msgEl.textContent = payload.message || "";
    badgesEl.innerHTML = "";
    if (payload.scan_status) {
      badgesEl.appendChild(
        badge(
          "AV: " + payload.scan_status,
          payload.scan_status === "clean" || payload.scan_status === "skipped"
            ? "text-bg-success"
            : "text-bg-warning"
        )
      );
    }
    const summary = payload.summary || {};
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
    if ((summary.low_confidence_fields || []).length) {
      badgesEl.appendChild(
        badge("baixa confiança: " + summary.low_confidence_fields.join(", "), "text-bg-warning")
      );
    }

    highlightsEl.innerHTML = "";
    row("Marca", ex.brand || ex.manufacturer);
    row("Modelo", ex.model_code);
    row("SKU sugerido", ex.sku_suggestion);
    row("Categoria", ex.category || ex.category_hint);
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
  }

  function setField(name, value) {
    if (value === null || value === undefined || value === "") return;
    const el = document.getElementById("id_" + name) || document.querySelector('[name="' + name + '"]');
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = Boolean(value);
      return;
    }
    el.value = value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function applySuggestions(sug) {
    if (!sug) return;
    setField("sku", sug.sku);
    setField("brand_ref", sug.brand_ref);
    setField("equipment_model", sug.equipment_model);
    setField("name", sug.name);
    setField("description", sug.description);
    setField("voltage", sug.voltage);
    setField("product_kind", sug.product_kind);
    setField("status", sug.status || "draft");
    setField("category", sug.category);
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
        "Análise concluída. Revise a proposta abaixo — nada foi aplicado ainda.",
        "ok"
      );
      showAgent(data);
    } catch (err) {
      setStatus("Erro de rede ao enviar o PDF.", "error");
    } finally {
      analyzeBtn.disabled = false;
    }
  });

  approveBtn.addEventListener("click", function () {
    if (!current) return;
    applySuggestions(current.form_suggestions || {});
    if (extractionField) extractionField.value = String(current.extraction_id || "");
    setStatus(
      "Proposta aprovada e copiada para o formulário. Revise os campos e clique em Salvar quando estiver pronto.",
      "ok"
    );
    const form = document.getElementById("product-main-form");
    if (form) form.scrollIntoView({ behavior: "smooth", block: "start" });
  });

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
