function setStatus(message, type = "info") {
  const status = document.getElementById("status");
  if (!message) {
    status.hidden = true;
    status.textContent = "";
    status.dataset.type = "";
    return;
  }

  status.hidden = false;
  status.textContent = message;
  status.dataset.type = type;
}

async function fetchText(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Fetch failed: ${res.status} ${res.statusText}`);
  }
  return await res.text();
}

async function getMarked() {
  // Prefer global UMD build if present
  if (globalThis.marked && typeof globalThis.marked.parse === "function") {
    return globalThis.marked;
  }

  throw new Error(
    "Markdown 解析器 marked 未加载（请检查 index.html 是否成功加载 ./vendor/marked.min.js）。"
  );
}

function parseMarkdown(markedLib, markdown) {
  const options = {
    gfm: true,
    breaks: true,
    headerIds: true,
    mangle: false,
  };

  if (markedLib && typeof markedLib.parse === "function") {
    return markedLib.parse(markdown, options);
  }
  if (typeof markedLib === "function") {
    return markedLib(markdown, options);
  }

  throw new Error("marked 已加载但未暴露 parse()。");
}

async function renderMarkdown(markdown) {
  const markedLib = await getMarked();
  const html = parseMarkdown(markedLib, markdown);

  const purifier = globalThis.DOMPurify;
  if (!purifier || typeof purifier.sanitize !== "function") {
    throw new Error("HTML 清洗器 DOMPurify 未加载。");
  }

  const clean = purifier.sanitize(html, {
    USE_PROFILES: { html: true },
  });

  const content = document.getElementById("content");
  content.innerHTML = clean;
}

async function loadReport(reportPath) {
  setStatus(`正在加载：${reportPath}`);

  try {
    const markdown = await fetchText(reportPath);
    await renderMarkdown(markdown);
    setStatus(`已加载：${reportPath}`);
  } catch (err) {
    console.error(err);
    setStatus(`加载失败：${reportPath}。${err?.message || err}`, "error");

    const content = document.getElementById("content");
    content.innerHTML = "";
  }
}

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// 只看高影响：从 report.json 里挑出影响等级为「高」的热点，按行业列出
async function renderHighImpact() {
  setStatus("正在加载：report.json");
  try {
    const res = await fetch("report.json", { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`Fetch failed: ${res.status} ${res.statusText}`);
    }
    const report = await res.json();
    const parts = [`<h1>${escapeHtml(report.title)} · 只看高影响</h1>`];
    let count = 0;
    for (const topic of report.topics) {
      const high = topic.hotspots.filter((h) => h.level === "高");
      if (!high.length) continue;
      parts.push(`<h2>${escapeHtml(topic.name)}</h2>`);
      for (const h of high) {
        count += 1;
        const refs = h.references
          .map((r) => `<a href="${escapeHtml(r.url)}" target="_blank" rel="noreferrer">${escapeHtml(r.source)}</a>`)
          .join("；");
        parts.push(
          `<h3>${escapeHtml(h.title)} <code>${escapeHtml(h.impact_area)}·高</code></h3>` +
            `<ul><li>发生了什么：${escapeHtml(h.what_happened)}</li>` +
            `<li>对我们的影响：${escapeHtml(h.impact)}</li><li>来源：${refs}</li></ul>`,
        );
      }
    }
    if (!count) parts.push("<p>本周没有影响等级为「高」的热点。</p>");
    document.getElementById("content").innerHTML = globalThis.DOMPurify.sanitize(parts.join(""));
    setStatus(`只看高影响：共 ${count} 条`);
  } catch (err) {
    console.error(err);
    setStatus(`加载失败：report.json。${err?.message || err}`, "error");
  }
}

function wireUi() {
  const toggle = document.getElementById("high-only");
  toggle.addEventListener("change", () => (toggle.checked ? renderHighImpact() : loadReport("report.md")));
  loadReport("report.md");
}

wireUi();
