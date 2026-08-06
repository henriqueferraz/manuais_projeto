(() => {
  const root = document.getElementById("tp-chat");
  if (!root) return;

  const body = document.getElementById("tp-chat-body");
  const form = document.getElementById("tp-chat-form");
  const input = document.getElementById("tp-chat-input");
  const typing = document.getElementById("tp-chat-typing");
  const streamUrl = root.dataset.streamUrl;
  const feedbackUrl = root.dataset.feedbackUrl;
  const csrf = root.dataset.csrf;
  const productId = root.dataset.productId || "";
  let sessionId = null;

  function scrollBottom() {
    body.scrollTop = body.scrollHeight;
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function addBubble(role, text) {
    const bubble = el("div", `tp-chat__bubble tp-chat__bubble--${role}`);
    bubble.textContent = text;
    body.appendChild(bubble);
    scrollBottom();
    return bubble;
  }

  function renderSources(bubble, sources) {
    if (!sources || !sources.length) return;
    const wrap = el("div", "tp-chat__source");
    sources.forEach((src) => {
      const tag = el(
        "span",
        "tp-chat__source-tag",
        `Fonte técnica: ${src.section || "Manual"}${src.page ? `, pág. ${src.page}` : ""}`
      );
      tag.title = src.excerpt || "";
      wrap.appendChild(tag);
    });
    bubble.appendChild(wrap);
  }

  function renderFeedback(bubble, messageId) {
    const bar = el("div", "tp-feedback");
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Avaliar resposta");

    const up = el("button", "", "👍 Útil");
    up.type = "button";
    up.setAttribute("aria-label", "Marcar como útil");
    const down = el("button", "", "👎 Não útil");
    down.type = "button";
    down.setAttribute("aria-label", "Marcar como não útil");

    async function send(vote) {
      if (bar.classList.contains("is-locked")) return;
      bar.classList.add("is-locked");
      up.classList.toggle("is-active", vote === "up");
      down.classList.toggle("is-active", vote === "down");
      try {
        const res = await fetch(feedbackUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify({ message_id: messageId, vote }),
        });
        const data = await res.json();
        if (data.ticket_code) {
          const note = el(
            "div",
            "tp-chat__meta",
            `Chamado ${data.ticket_code} aberto com o histórico desta conversa.`
          );
          bubble.appendChild(note);
        }
      } catch (_) {
        bar.classList.remove("is-locked");
      }
    }

    up.addEventListener("click", () => send("up"));
    down.addEventListener("click", () => send("down"));
    bar.appendChild(up);
    bar.appendChild(down);
    bubble.appendChild(bar);
  }

  function setTyping(on) {
    typing.classList.toggle("d-none", !on);
    typing.setAttribute("aria-hidden", on ? "false" : "true");
    scrollBottom();
  }

  async function streamAnswer(question) {
    addBubble("user", question);
    const aiBubble = addBubble("ai", "");
    setTyping(true);
    input.disabled = true;

    let full = "";
    let messageId = null;
    let sources = [];

    try {
      const res = await fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          product_id: productId || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Falha no chat." }));
        aiBubble.textContent = err.detail || "Não foi possível responder agora.";
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const block of parts) {
          const lines = block.split("\n");
          let event = "message";
          let dataLine = "";
          for (const line of lines) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            if (line.startsWith("data:")) dataLine += line.slice(5).trim();
          }
          if (!dataLine) continue;
          let data;
          try {
            data = JSON.parse(dataLine);
          } catch {
            continue;
          }
          if (event === "meta") {
            sessionId = data.session_id || sessionId;
            messageId = data.message_id;
            sources = data.sources || [];
          } else if (event === "token") {
            full += data.text || "";
            aiBubble.textContent = full;
            scrollBottom();
          } else if (event === "done") {
            full = data.content || full;
            aiBubble.textContent = full;
            messageId = data.message_id || messageId;
            sources = data.sources || sources;
            setTyping(false);
            renderSources(aiBubble, sources);
            if (messageId) renderFeedback(aiBubble, messageId);
          }
        }
      }
    } catch (_) {
      aiBubble.textContent = "Falha de conexão. Tente novamente.";
    } finally {
      setTyping(false);
      input.disabled = false;
      input.focus();
      scrollBottom();
    }
  }

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const q = (input.value || "").trim();
    if (!q) return;
    input.value = "";
    streamAnswer(q);
  });

  // Evita zoom iOS em focus; garante input visível
  input.addEventListener("focus", () => {
    setTimeout(scrollBottom, 300);
  });
})();
