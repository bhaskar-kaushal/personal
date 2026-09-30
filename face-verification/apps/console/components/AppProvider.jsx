"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getGallery, getHealth } from "@/lib/api";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

export default function AppProvider({ children }) {
  const [gallery, setGallery] = useState(null);      // string[] | null
  const [galleryError, setGalleryError] = useState(null);
  const [health, setHealth] = useState({ state: "checking" });
  const [toasts, setToasts] = useState([]);
  const [dialog, setDialog] = useState(null);
  const toastId = useRef(0);

  const refreshGallery = useCallback(async () => {
    try {
      const { person_ids } = await getGallery();
      const sorted = [...person_ids].sort((a, b) => a.localeCompare(b));
      setGallery(sorted);
      setGalleryError(null);
      return sorted;
    } catch (e) {
      setGalleryError(e.message);
      return null;
    }
  }, []);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const body = await getHealth();
        if (alive) setHealth({ state: body.gallery_size == null ? "degraded" : "ok" });
      } catch {
        if (alive) setHealth({ state: "down" });
      }
    };
    poll();
    refreshGallery();
    const t = setInterval(poll, 30000);
    return () => { alive = false; clearInterval(t); };
  }, [refreshGallery]);

  const toast = useCallback((message, kind = "") => {
    const id = ++toastId.current;
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);

  const confirm = useCallback((opts) => new Promise((resolve) => setDialog({ ...opts, resolve })), []);
  const closeDialog = (value) => { dialog.resolve(value); setDialog(null); };

  return (
    <Ctx.Provider value={{ gallery, galleryError, refreshGallery, health, toast, confirm }}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => <div key={t.id} className={`toast ${t.kind}`}>{t.message}</div>)}
      </div>
      {dialog && <ConfirmDialog dialog={dialog} onClose={closeDialog} />}
    </Ctx.Provider>
  );
}

function ConfirmDialog({ dialog, onClose }) {
  const ref = useRef(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  const body = [].concat(dialog.body || []);
  return (
    <dialog ref={ref} aria-labelledby="dlg-title" onCancel={() => onClose(false)}>
      <div className="card-b">
        <h2 id="dlg-title">{dialog.title}</h2>
        <div style={{ marginTop: 8 }}>{body.map((p, i) => <p key={i}>{p}</p>)}</div>
      </div>
      <div className="actions">
        <button className="btn" onClick={() => onClose(false)}>Cancel</button>
        <button className={`btn ${dialog.danger ? "danger" : "primary"}`} onClick={() => onClose(true)}>
          {dialog.confirmLabel || "Confirm"}
        </button>
      </div>
    </dialog>
  );
}
