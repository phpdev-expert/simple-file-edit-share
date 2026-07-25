// Client-side export helpers: HTML content -> Markdown download or PDF (print).
import TurndownService from "turndown";

const turndown = new TurndownService({ headingStyle: "atx", bulletListMarker: "-" });

function download(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function exportMarkdown(title: string, html: string) {
  const md = `# ${title}\n\n${turndown.turndown(html)}\n`;
  download(`${safe(title)}.md`, md, "text/markdown");
}

// PDF via the browser print dialog. We render the content into an off-screen
// iframe (srcdoc, no document.write) and print just that frame, so the app
// chrome never bleeds into the output.
export function exportPdf(title: string, html: string) {
  const doc = `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
    <style>
      body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.6; max-width: 700px; margin: 2rem auto; padding: 0 1rem; color: #1a1c1f; }
      h1 { font-size: 1.9rem; } h2 { font-size: 1.4rem; }
      ul, ol { padding-left: 1.4rem; }
    </style></head><body><h1>${escapeHtml(title)}</h1>${html}</body></html>`;

  const frame = document.createElement("iframe");
  frame.setAttribute("srcdoc", doc);
  frame.style.position = "fixed";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.width = "0";
  frame.style.height = "0";
  frame.style.border = "0";
  frame.onload = () => {
    const win = frame.contentWindow;
    if (win) {
      win.focus();
      win.print();
    }
    // Remove after the print dialog has had a chance to capture the frame.
    setTimeout(() => frame.remove(), 1000);
  };
  document.body.appendChild(frame);
}

function safe(name: string) {
  return name.replace(/[^a-z0-9-_ ]/gi, "").trim() || "document";
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
}
