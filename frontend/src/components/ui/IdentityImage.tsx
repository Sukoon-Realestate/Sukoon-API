"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL, isBackendEnabled } from '@/lib/api/config';

/** Read protected proof bytes with the current session; never persist or redirect. */
export function IdentityImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const { user } = useAuth();
  const [result, setResult] = useState<{ source: string; actor: string; url?: string; error?: boolean } | null>(null);
  const live = isBackendEnabled();
  const actor = user?.id ?? '';
  useEffect(() => {
    if (!live || !actor) return;
    const abort = new AbortController();
    let objectUrl: string | undefined;
    const read = async () => {
      try {
        if (!/^\/api\/v1\/admin\/kyc\/[0-9a-f-]+\/media\/(id_face|id_back|confirmation_selfi)\/$/.test(src)) throw new Error('Unsupported identity destination');
        const token = localStorage.getItem('sukoon_access_token');
        const response = await fetch(`${API_BASE_URL}${src}`, {
          credentials: 'include', cache: 'no-store', signal: abort.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!response.ok || !response.headers.get('content-type')?.startsWith('image/')) throw new Error('Evidence read unconfirmed');
        const blob = await response.blob();
        if (blob.size > 10 * 1024 * 1024) throw new Error('Evidence exceeds the read limit');
        if (abort.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob);
        setResult({ source: src, actor, url: objectUrl });
      } catch {
        if (!abort.signal.aborted) setResult({ source: src, actor, error: true });
      }
    };
    void read();
    return () => { abort.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [src, actor, live]);
  if (!live) return <img src={src} alt={alt} className={className} />;
  const current = result?.source === src && result.actor === actor ? result : null;
  if (current?.url) return <img src={current.url} alt={alt} className={className} />;
  return <span role="status">{current?.error ? 'تعذّر تحميل المستند المحمي. أعد فتح المراجعة للمحاولة.' : 'جاري تحميل المستند المحمي…'}</span>;
}
