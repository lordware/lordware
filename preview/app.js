"use strict";

const article = document.getElementById("readme");
const status = document.getElementById("preview-status");
const frame = document.querySelector(".profile-frame");
const state = { version: "after", size: "desktop", theme: "dark" };
let requestNumber = 0;

function escapeHTML(text) {
  return text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

// The redesign uses trusted repository HTML. These two Markdown forms are all
// the original README needs; this is deliberately not a general Markdown parser.
function renderReadme(text) {
  let fence = false;
  let code = [];
  const output = [];
  for (const line of text.split(/\r?\n/)) {
    if (/^```/.test(line)) {
      if (fence) output.push(`<pre><code>${escapeHTML(code.join("\n"))}\n</code></pre>`);
      code = [];
      fence = !fence;
      continue;
    }
    if (fence) {
      code.push(line);
      continue;
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) {
      const label = escapeHTML(heading[2]).replace(/`([^`]+)`/g, "<code>$1</code>");
      output.push(`<h${heading[1].length}>${label}</h${heading[1].length}>`);
    } else {
      output.push(line);
    }
  }
  if (fence) output.push(`<pre><code>${escapeHTML(code.join("\n"))}</code></pre>`);
  return output.join("\n");
}

function applyTheme() {
  document.documentElement.dataset.theme = state.theme;
  const width = state.size === "mobile" ? Math.min(375, window.innerWidth) : window.innerWidth;
  // Replace only simulated features, then let the browser evaluate the complete
  // query (including and/or/not). Always start from the untouched original.
  const condition = matches => matches ? "(min-width: 0px)" : "(max-width: 0px)";
  article.querySelectorAll("picture source[media]").forEach(source => {
    const original = source.dataset.originalMedia ?? source.media;
    source.dataset.originalMedia = original;
    const simulated = original
      .replace(/\(prefers-color-scheme:\s*(dark|light)\)/gi, (_, scheme) => condition(scheme.toLowerCase() === state.theme))
      .replace(/\((?:(min|max)-)?width:\s*([\d.]+)(px|em|rem)\)/gi, (_, bound, amount, unit) => {
        // em/rem in media queries use the browser's initial font size (16 px).
        const limit = Number(amount) * (unit.toLowerCase() === "px" ? 1 : 16);
        return condition(bound?.toLowerCase() === "min" ? width >= limit : bound?.toLowerCase() === "max" ? width <= limit : width === limit);
      });
    source.media = window.matchMedia(simulated).matches ? "all" : "not all";
  });
}

function describe() {
  const version = state.version === "after" ? "Working README" : "Original README at HEAD";
  const width = state.size === "mobile" ? "375 px frame, fitted to your screen" : "896 px GitHub-style frame";
  status.textContent = `${version} · ${width} · ${state.theme} theme`;
}

async function loadReadme() {
  const request = ++requestNumber;
  article.setAttribute("aria-busy", "true");
  status.textContent = "Loading the local README…";
  try {
    const response = await fetch(`/api/readme?version=${state.version}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const { content } = await response.json();
    if (request !== requestNumber) return;
    article.innerHTML = renderReadme(content);
    applyTheme();
    describe();
  } catch (error) {
    if (request !== requestNumber) return;
    article.replaceChildren();
    status.textContent = `Could not load the README. ${error.message}. Use Refresh to try again.`;
  } finally {
    if (request === requestNumber) article.setAttribute("aria-busy", "false");
  }
}

for (const key of ["version", "size", "theme"]) {
  document.querySelectorAll(`button[data-${key}]`).forEach(button => {
    button.addEventListener("click", () => {
      state[key] = button.dataset[key];
      document.querySelectorAll(`button[data-${key}]`).forEach(peer => {
        peer.setAttribute("aria-pressed", String(peer === button));
      });
      if (key === "version") loadReadme();
      else {
        frame.dataset.size = state.size;
        applyTheme();
        describe();
      }
    });
  });
}
document.getElementById("refresh").addEventListener("click", loadReadme);
window.addEventListener("resize", applyTheme);
loadReadme();
