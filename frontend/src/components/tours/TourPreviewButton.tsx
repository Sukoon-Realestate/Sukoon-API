'use client';

import { useEffect, useRef, useState } from 'react';
import { previewTour, TourReview } from '../../lib/api/tour-review';

type PreviewWindow = Window & {
  sokounTour?: { ready: () => void; receive: (message: unknown) => void };
  SokounTour?: { postMessage: (message: string) => void };
};

export function TourPreviewButton({ item, context }: { item: TourReview; context: string }) {
  const cleanup = useRef<(() => void) | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => () => cleanup.current?.(), []);
  async function open() {
    if (busy) return;
    cleanup.current?.();
    const popup = window.open('about:blank', '_blank') as PreviewWindow | null;
    if (!popup) { setMessage('اسمح بفتح نافذة المعاينة ثم حاول مجددًا.'); return; }
    setBusy(true); setMessage('جارٍ فتح المعاينة الخاصة…');
    let closed = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    cleanup.current = () => { closed = true; clearInterval(timer); popup.close(); };
    try {
      const session = await previewTour(item, context);
      if (closed) return;
      const url = new URL(session.viewer_url);
      if (url.origin !== window.location.origin || url.protocol !== 'https:' || url.pathname !== '/tours/' || url.search || url.hash) {
        throw new Error('معاينة الجولة تحتاج عارض الجولات على نفس عنوان HTTPS للوحة الإدارة. يظل قرار المراجعة بانتظار فحص المخرجات.');
      }
      popup.location.href = url.href;
      let initialized = false;
      timer = setInterval(() => {
        if (popup.closed || Date.parse(session.bootstrap_expires_at) <= Date.now()) {
          clearInterval(timer); if (!closed) setMessage('أُغلقت المعاينة أو انتهت مهلتها. افتحها مجددًا.'); return;
        }
        try {
          if (popup.location.href !== url.href || !popup.sokounTour) return;
          popup.SokounTour = { postMessage(raw: string) {
            if (closed || typeof raw !== 'string' || raw.length > 16384) return;
            const value = JSON.parse(raw);
            if (initialized) {
              if (value.type === 'requestClose' && value.session_id === session.session_id) popup.close();
              return;
            }
            if (value.protocol_version !== 1 || value.type !== 'viewerReady' || typeof value.viewer_instance_id !== 'string') return;
            initialized = true;
            popup.sokounTour?.receive({ protocol_version: 1, type: 'initialize', message_id: crypto.randomUUID(),
              viewer_instance_id: value.viewer_instance_id, session_id: session.session_id,
              payload: { session_id: session.session_id, bootstrap_token: session.bootstrap_token, language: 'ar',
                reduced_motion: matchMedia('(prefers-reduced-motion: reduce)').matches } });
            session.bootstrap_token = ''; clearInterval(timer); setMessage('فُتحت المعاينة الخاصة. افحص نطاق العرض والمخرجات قبل اتخاذ القرار.');
          } };
          popup.sokounTour.ready();
        } catch { clearInterval(timer); setMessage('تعذّر الاتصال بالعارض. أغلق المعاينة وافتحها مجددًا بعد مراجعة إعدادها.'); }
      }, 150);
    } catch (error) {
      popup.close(); if (!closed) setMessage(error instanceof Error ? error.message : 'تعذّر فتح المعاينة.');
    } finally { if (!closed) setBusy(false); }
  }
  return <div className="space-y-2"><button type="button" disabled={busy} onClick={() => void open()} className="rounded border px-4 py-2">فتح المعاينة الخاصة</button><p role="status">{message}</p></div>;
}
