/**
 * Busca fotos na internet no cadastro de produto (HITL).
 * Lê marca / modelo / categoria → até 5 opções → usuário marca uma ou mais para inserir.
 */
(function () {
  const root = document.getElementById("product-web-photos");
  if (!root) return;

  const searchUrl = root.dataset.searchUrl;
  const csrf = root.dataset.csrf;
  const maxSelect = Math.max(1, parseInt(root.dataset.maxSelect || "5", 10) || 5);
  const searchBtn = document.getElementById("product-web-photos-search");
  const statusEl = document.getElementById("product-web-photos-status");
  const resultsEl = document.getElementById("product-web-photos-results");
  const hiddenWrap = document.getElementById("product-web-photos-hidden");

  function fieldValue(id) {
    const el = document.getElementById(id);
    return el ? String(el.value || "").trim() : "";
  }

  function setStatus(text, kind) {
    if (!statusEl) return;
    statusEl.hidden = !text;
    statusEl.textContent = text || "";
    statusEl.className = "small mb-2";
    if (kind === "error") statusEl.classList.add("text-danger");
    else if (kind === "ok") statusEl.classList.add("text-success");
    else statusEl.classList.add("text-secondary");
  }

  function selectedCheckboxes() {
    if (!resultsEl) return [];
    return Array.prototype.slice.call(
      resultsEl.querySelectorAll('input[name="web_image_choice"]:checked')
    );
  }

  function syncHiddenUrls() {
    if (!hiddenWrap) return;
    hiddenWrap.innerHTML = "";
    selectedCheckboxes().forEach(function (input) {
      const url = String(input.value || "").trim();
      if (!url) return;
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = "web_image_urls";
      hidden.value = url;
      hiddenWrap.appendChild(hidden);
    });
  }

  function updateSelectionHint() {
    const n = selectedCheckboxes().length;
    if (!n) {
      setStatus("Nenhuma foto marcada. Você pode marcar várias antes de salvar.", "");
      return;
    }
    setStatus(
      n === 1
        ? "1 foto marcada — será inserida ao salvar (se houver vaga na galeria)."
        : n + " fotos marcadas — serão inseridas ao salvar (respeitando o limite da galeria).",
      "ok"
    );
  }

  function renderCandidates(payload) {
    if (!resultsEl) return;
    resultsEl.innerHTML = "";
    const candidates = (payload && payload.candidates) || [];
    if (!candidates.length) {
      resultsEl.hidden = true;
      syncHiddenUrls();
      return;
    }

    candidates.forEach(function (item, idx) {
      const card = document.createElement("label");
      card.className = "tp-web-photos__card";

      const check = document.createElement("input");
      check.type = "checkbox";
      check.name = "web_image_choice";
      check.value = item.image_url || "";
      check.addEventListener("change", function () {
        const selected = selectedCheckboxes();
        if (check.checked && selected.length > maxSelect) {
          check.checked = false;
          setStatus(
            "Limite de " + maxSelect + " fotos por busca (máximo da galeria).",
            "error"
          );
          return;
        }
        syncHiddenUrls();
        updateSelectionHint();
      });

      const preview = document.createElement("span");
      preview.className = "tp-web-photos__preview";
      const img = document.createElement("img");
      img.src = item.thumbnail_url || item.image_url || "";
      img.alt = item.title || "Sugestão de foto";
      img.loading = "lazy";
      img.referrerPolicy = "no-referrer";
      img.onerror = function () {
        preview.classList.add("tp-web-photos__preview--empty");
        preview.textContent = "";
        const icon = document.createElement("span");
        icon.className = "material-symbols-outlined";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = "broken_image";
        preview.appendChild(icon);
      };
      preview.appendChild(img);

      const caption = document.createElement("span");
      caption.className = "tp-web-photos__caption";
      caption.textContent = item.title || "Opção " + (idx + 1);

      card.appendChild(check);
      card.appendChild(preview);
      card.appendChild(caption);
      resultsEl.appendChild(card);
    });

    resultsEl.hidden = false;
    syncHiddenUrls();
  }

  async function runSearch() {
    if (!searchUrl) return;
    const brandRef = fieldValue("id_brand_ref");
    const equipmentModel = fieldValue("id_equipment_model");
    const category = fieldValue("id_category");
    const name = fieldValue("id_name");

    if (!brandRef && !equipmentModel && !category && !name) {
      setStatus("Preencha marca, modelo ou categoria antes de buscar.", "error");
      return;
    }

    const fd = new FormData();
    fd.append("brand_ref", brandRef);
    fd.append("equipment_model", equipmentModel);
    fd.append("category", category);
    fd.append("name", name);

    searchBtn.disabled = true;
    setStatus("Buscando fotos na internet…", "");
    try {
      const res = await fetch(searchUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrf || "" },
        body: fd,
        credentials: "same-origin",
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setStatus((data && data.error) || "Falha ao buscar fotos.", "error");
        renderCandidates({ candidates: [] });
        return;
      }
      renderCandidates(data);
      setStatus(
        data.message ||
          "Marque uma ou mais fotos para inserir ao salvar (ou nenhuma).",
        "ok"
      );
    } catch (err) {
      setStatus("Erro de rede ao buscar fotos.", "error");
      renderCandidates({ candidates: [] });
    } finally {
      searchBtn.disabled = false;
    }
  }

  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      runSearch();
    });
  }
})();
