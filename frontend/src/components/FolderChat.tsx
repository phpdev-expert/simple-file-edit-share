import { useEffect, useRef, useState } from "react";
import { api, ApiError, ChatMessage } from "../api";
import { IconSparkles } from "./icons";

interface Msg extends ChatMessage {
  sources?: string[];
}

export default function FolderChat({
  folderId,
  folderName,
  onClose,
}: {
  folderId: number;
  folderName: string;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    const history: ChatMessage[] = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.chatFolder(folderId, text, history);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Something went wrong.";
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${msg}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-head">
        <div className="chat-title">
          <IconSparkles size={18} /> Chat with <strong>{folderName}</strong>
        </div>
        <button className="icon-btn" onClick={onClose} title="Close">
          ✕
        </button>
      </div>

      <div className="chat-body" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-hint">
            Ask anything about the documents in <strong>{folderName}</strong>. Answers are grounded
            in this folder's contents.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <div className="chat-bubble">{m.content}</div>
            {m.sources && m.sources.length > 0 && (
              <div className="chat-sources">Sources: {m.sources.join(", ")}</div>
            )}
          </div>
        ))}
        {busy && (
          <div className="chat-msg assistant">
            <div className="chat-bubble typing">Thinking…</div>
          </div>
        )}
      </div>

      <form className="chat-input" onSubmit={send}>
        <input
          placeholder="Ask about this folder…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          autoFocus
        />
        <button className="btn-primary" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
