'use client';
import { useEffect, useState } from 'react';
import { API_BASE_URL, isBackendEnabled } from '@/lib/api/config';
export function PolicyMedia({ caseId, mediaId, kind }: { caseId: string; mediaId: string; kind: string }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [requested, setRequested] = useState(false);
  useEffect(() => {
    if (!requested || !isBackendEnabled()) return;
    const abort = new AbortController();
    let objectUrl = '';
    const token = localStorage.getItem('sukoon_access_token');
    fetch(`${API_BASE_URL}/api/v1/chat/admin/policy-cases/${caseId}/attachments/${mediaId}/`, { headers: { Authorization: `Bearer ${token ?? ''}` }, signal: abort.signal, credentials: 'include', cache: 'no-store' })
      .then(async response => {
        if (!response.ok || !['image/jpeg', 'audio/mp4'].includes(response.headers.get('content-type') ?? '')) throw new Error('unavailable');
        const data = await response.blob();
        if (abort.signal.aborted || localStorage.getItem('sukoon_access_token') !== token) return;
        objectUrl = URL.createObjectURL(data); setUrl(objectUrl);
      }).catch(() => { if (!abort.signal.aborted) setError('المرفق غير متاح للمراجعة حاليًا.'); });
    return () => { abort.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [caseId, mediaId, requested]);
  if (!requested) return <button className="underline min-h-12" onClick={() => setRequested(true)}>عرض المرفق الأصلي للمراجعة</button>;
  if (error) return <p role="alert">{error}</p>;
  if (!url) return <p>جارٍ تحميل المرفق…</p>;
  // Authenticated private blobs never expose storage credentials or public URLs.
  return kind === 'voice' ? <audio controls src={url} preload="metadata" /> : <img src={url} alt="مرفق الحالة الأصلي" className="max-h-96 object-contain" />;
}
