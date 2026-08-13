(() => {
  function boot() {
    const wrap = document.getElementById("mp-brick-wrap");
    if (!wrap || wrap.dataset.mpBooted === "1") return;
    wrap.dataset.mpBooted = "1";

    const publicKey = wrap.dataset.mpPublicKey || "";
    const amount = Number(String(wrap.dataset.mpAmount || "0").replace(",", "."));
    const email = wrap.dataset.mpEmail || "";
    const payUrl = wrap.dataset.mpPayUrl || "";
    const errBox = document.getElementById("mp-brick-error");
    const statusBox = document.getElementById("mp-brick-status");

    function showError(msg) {
      if (statusBox) statusBox.hidden = true;
      if (!errBox) return;
      errBox.hidden = false;
      errBox.textContent = msg || "Falha no pagamento.";
    }

    function setStatus(msg) {
      if (!statusBox) return;
      statusBox.hidden = !msg;
      statusBox.textContent = msg || "";
    }

    function csrfToken() {
      const input = document.querySelector(
        "#mp-csrf-holder input[name=csrfmiddlewaretoken]"
      );
      return input ? input.value : "";
    }

    if (!publicKey || !(amount > 0) || !payUrl) {
      showError("Checkout Transparente mal configurado (chave ou valor).");
      return;
    }

    function mountBrick() {
      if (typeof MercadoPago === "undefined") {
        showError("SDK do Mercado Pago não carregou (CSP ou rede).");
        return;
      }
      setStatus("Carregando formulário de cartão…");
      const mp = new MercadoPago(publicKey, { locale: "pt-BR" });
      mp.bricks()
        .create("cardPayment", "cardPaymentBrick_container", {
          initialization: {
            amount,
            payer: email ? { email } : undefined,
          },
          customization: {
            visual: { style: { theme: "bootstrap" } },
            paymentMethods: { maxInstallments: 12 },
          },
          callbacks: {
            onReady: () => setStatus(""),
            onError: (error) => {
              showError((error && error.message) || "Erro no formulário de cartão.");
            },
            onSubmit: (cardData) => {
              return new Promise((resolve, reject) => {
                fetch(payUrl, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                  },
                  credentials: "same-origin",
                  body: JSON.stringify(cardData),
                })
                  .then(async (response) => {
                    const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.ok) {
                  const err = data.error || "Pagamento recusado.";
                  showError(
                    /live credentials/i.test(err)
                      ? "Credenciais de produção (APP_USR) não servem no Checkout Transparente. Use Access Token e Public Key de teste (TEST-) no .env."
                      : err
                  );
                  reject(data.error || response.statusText);
                  return;
                }
                    resolve();
                    window.location.assign(data.redirect || "/");
                  })
                  .catch((err) => {
                    showError("Falha de rede ao processar pagamento.");
                    reject(err);
                  });
              });
            },
          },
        })
        .then(() => setStatus(""))
        .catch((err) => {
          showError((err && err.message) || "Não foi possível carregar o Brick.");
        });
    }

    if (typeof MercadoPago !== "undefined") {
      mountBrick();
      return;
    }

    setStatus("Carregando SDK do Mercado Pago…");
    const existing = document.querySelector("script[data-mp-sdk='v2']");
    if (existing) {
      existing.addEventListener("load", mountBrick);
      existing.addEventListener("error", () =>
        showError("Falha ao carregar SDK do Mercado Pago.")
      );
      return;
    }

    const s = document.createElement("script");
    s.src = "https://sdk.mercadopago.com/js/v2";
    s.async = true;
    s.dataset.mpSdk = "v2";
    s.onload = mountBrick;
    s.onerror = () => showError("Falha ao carregar SDK do Mercado Pago.");
    document.head.appendChild(s);
  }

  document.body.addEventListener("htmx:afterSettle", boot);
  document.body.addEventListener("htmx:afterSwap", boot);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
