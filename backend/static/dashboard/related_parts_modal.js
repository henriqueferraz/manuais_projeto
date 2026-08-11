/**
 * Modal de peça vinculada — mostra informações sem sair do formulário do produto pai.
 */
(function () {
  const dataEl = document.getElementById("related-parts-data");
  const listEl = document.getElementById("related-parts-list");
  const modalEl = document.getElementById("related-part-modal");
  if (!dataEl || !listEl || !modalEl || !window.bootstrap) return;

  let partsById = {};
  try {
    const rows = JSON.parse(dataEl.textContent || "[]");
    rows.forEach(function (row) {
      partsById[String(row.id)] = row;
    });
  } catch (err) {
    return;
  }

  const titleEl = document.getElementById("related-part-modal-title");
  const brandEl = document.getElementById("related-part-modal-brand");
  const nameEl = document.getElementById("related-part-modal-name");
  const fieldsEl = document.getElementById("related-part-modal-fields");
  const descEl = document.getElementById("related-part-modal-description");
  const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);

  function addField(label, value) {
    if (value === null || value === undefined || value === "") return;
    const dt = document.createElement("dt");
    dt.className = "col-sm-4 text-secondary";
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.className = "col-sm-8 font-monospace mb-2";
    dd.textContent = String(value);
    fieldsEl.appendChild(dt);
    fieldsEl.appendChild(dd);
  }

  function showPart(part) {
    if (!part) return;
    titleEl.textContent = "Peça vinculada";
    brandEl.textContent = part.brand || "—";
    nameEl.textContent = part.name || part.sku || "—";
    fieldsEl.innerHTML = "";
    addField("SKU", part.sku);
    addField("Código da peça", part.part_code);
    addField("Modelo (produto pai)", part.equipment_model || part.model_code);
    addField("Categoria", part.category);
    addField("Status", part.status);
    addField("Preço", part.price != null && part.price !== "" ? "R$ " + part.price : "");
    addField("Ref. no diagrama", part.ref_number);
    addField("Qtd. por unidade", part.qty_per_unit);
    addField("SKU do produto pai", part.parent_sku);

    if (part.description) {
      descEl.hidden = false;
      descEl.textContent = part.description;
    } else {
      descEl.hidden = true;
      descEl.textContent = "";
    }
    modal.show();
  }

  listEl.addEventListener("click", function (event) {
    const btn = event.target.closest("[data-related-part-id]");
    if (!btn) return;
    const id = btn.getAttribute("data-related-part-id");
    showPart(partsById[String(id)]);
  });
})();
