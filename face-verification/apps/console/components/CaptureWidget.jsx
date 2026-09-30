"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from "react";
import Icon from "./Icon";
import { prepareImage } from "@/lib/image";

/**
 * Webcam + upload + drag-and-drop photo collector.
 * `max` = 1 behaves as a single replaceable photo; > 1 collects a list.
 * The parent reads photos through `onChange(blobs)` and can call `ref.clear()` / `ref.stopCamera()`.
 */
const CaptureWidget = forwardRef(function CaptureWidget({ max = 1, onChange }, ref) {
  const [items, setItems] = useState([]);           // { id, blob, url }
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [flashKey, setFlashKey] = useState(0);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const fileRef = useRef(null);
  const nextId = useRef(0);
  const itemsRef = useRef(items);
  itemsRef.current = items;

  const cameraSupported = typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia;

  const commit = useCallback((next) => {
    setItems(next);
    onChange?.(next.map((i) => i.blob));
  }, [onChange]);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setStreaming(false);
  }, []);

  const clear = useCallback(() => {
    itemsRef.current.forEach((i) => URL.revokeObjectURL(i.url));
    setError("");
    commit([]);
  }, [commit]);

  useImperativeHandle(ref, () => ({ clear, stopCamera }), [clear, stopCamera]);

  // Release the camera and object URLs when the widget unmounts.
  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    itemsRef.current.forEach((i) => URL.revokeObjectURL(i.url));
  }, []);

  // Attach the stream once the <video> element is rendered.
  useEffect(() => {
    if (streaming && videoRef.current && streamRef.current) videoRef.current.srcObject = streamRef.current;
  }, [streaming]);

  const push = useCallback((blob) => {
    const entry = { id: ++nextId.current, blob, url: URL.createObjectURL(blob) };
    const current = itemsRef.current;
    if (max === 1) {
      current.forEach((i) => URL.revokeObjectURL(i.url));
      commit([entry]);
    } else {
      commit([...current, entry]);
    }
  }, [max, commit]);

  const full = () => max > 1 && itemsRef.current.length >= max;

  async function toggleCamera() {
    if (streamRef.current) return stopCamera();
    setError("");
    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false,
      });
      setStreaming(true);
    } catch (e) {
      const name = e && e.name;
      setError(name === "NotAllowedError" || name === "SecurityError"
        ? "Camera permission was denied. Allow camera access in your browser, or upload a photo instead."
        : name === "NotFoundError"
          ? "No camera was found on this device. Upload a photo instead."
          : "The camera could not be started. Upload a photo instead.");
    }
  }

  async function snap() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    if (full()) return setError(`Up to ${max} photos.`);
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    setFlashKey((k) => k + 1);
    const blob = await new Promise((r) => canvas.toBlob(r, "image/jpeg", 0.9));
    if (blob) push(blob);
  }

  async function addFiles(files) {
    setError("");
    const images = files.filter((f) => f.type.startsWith("image/"));
    if (images.length !== files.length) setError("Only image files are accepted.");
    for (const f of images) {
      if (full()) { setError(`Up to ${max} photos.`); break; }
      try { push(await prepareImage(f)); } catch (e) { setError(e.message); }
    }
  }

  function remove(id) {
    const gone = items.find((i) => i.id === id);
    if (gone) URL.revokeObjectURL(gone.url);
    setError("");
    commit(items.filter((i) => i.id !== id));
  }

  const single = max === 1 && items.length === 1;

  return (
    <div className="capture">
      <div
        className={`stage${dragging ? " drag" : ""}`}
        onDragEnter={(e) => { e.preventDefault(); setDragging(true); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragging(false); }}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles([...e.dataTransfer.files]); }}
      >
        {streaming && <video ref={videoRef} className="mirror" autoPlay playsInline muted aria-label="Live camera preview" />}
        {streaming && <div className="guide" aria-hidden="true"><i /></div>}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {!streaming && single && <img className="preview" src={items[0].url} alt="Selected photo" />}
        {!streaming && !single && (
          <div className="placeholder">
            <Icon name="face" size={44} />
            <div>{max > 1 ? "Start the camera or add photos" : "Start the camera or add a photo"}</div>
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>Drag &amp; drop an image here</div>
          </div>
        )}
        <div key={flashKey} className={`flash${flashKey ? " on" : ""}`} />
      </div>

      <div className="capture-actions">
        <button type="button" className="btn" onClick={toggleCamera} disabled={!cameraSupported}
          title={cameraSupported ? undefined : "Camera unavailable (needs HTTPS and a supported browser)"}>
          <Icon name="camera" />{streaming ? "Stop camera" : "Start camera"}
        </button>
        {streaming && <button type="button" className="btn primary" onClick={snap}><Icon name="camera" />Capture</button>}
        <button type="button" className="btn" onClick={() => fileRef.current?.click()}><Icon name="upload" />Upload</button>
        {items.length > 0 && <button type="button" className="btn ghost" onClick={clear}>Clear</button>}
        <input ref={fileRef} type="file" accept="image/*" multiple={max > 1} className="sr-only" tabIndex={-1}
          onChange={(e) => { addFiles([...e.target.files]); e.target.value = ""; }} />
      </div>

      {error && <div className="notice bad" role="alert"><Icon name="alert" /><div>{error}</div></div>}

      {max > 1 && items.length > 0 && (
        <div className="thumbs" aria-label="Captured photos">
          {items.map((it, i) => (
            <div key={it.id} className="thumb">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={it.url} alt={`Photo ${i + 1}`} />
              <button type="button" aria-label={`Remove photo ${i + 1}`} onClick={() => remove(it.id)}>×</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

export default CaptureWidget;

export function CaptureTips() {
  return (
    <ul className="tips" style={{ marginTop: 12 }}>
      <li>Face the camera directly</li><li>Even, front-facing light</li>
      <li>One person in frame</li><li>No sunglasses or mask</li>
    </ul>
  );
}
