// Live presence + content sync for a document over a WebSocket.
// Persistence still flows through REST autosave; this only propagates live state.
import { useEffect, useRef, useState } from "react";
import { Editor } from "@tiptap/react";
import { getAuthToken } from "./api";

export interface Participant {
  id: number;
  name: string;
  role: string;
}

export function useDocRealtime(docId: number, editor: Editor | null, enabled: boolean) {
  const [presence, setPresence] = useState<Participant[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const applyingRemote = useRef(false);
  const lastLocalEdit = useRef(0);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Open the socket and handle incoming presence / update messages.
  useEffect(() => {
    if (!editor || !docId) return;
    const token = getAuthToken();
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws/documents/${docId}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      let msg: any;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      if (msg.type === "presence") {
        setPresence(msg.users || []);
      } else if (msg.type === "update") {
        // Don't clobber the user mid-keystroke (last-writer-wins otherwise).
        if (Date.now() - lastLocalEdit.current < 1500) return;
        applyingRemote.current = true;
        editor.commands.setContent(msg.html || "<p></p>", false);
        applyingRemote.current = false;
      }
    };
    ws.onclose = () => {
      if (wsRef.current === ws) wsRef.current = null;
    };

    return () => ws.close();
  }, [docId, editor]);

  // Broadcast local edits (debounced), unless we're applying a remote update.
  useEffect(() => {
    if (!editor || !enabled) return;
    const onUpdate = () => {
      if (applyingRemote.current) return;
      lastLocalEdit.current = Date.now();
      if (sendTimer.current) clearTimeout(sendTimer.current);
      sendTimer.current = setTimeout(() => {
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "update", html: editor.getHTML() }));
        }
      }, 350);
    };
    editor.on("update", onUpdate);
    return () => {
      editor.off("update", onUpdate);
    };
  }, [editor, enabled]);

  return { presence };
}
