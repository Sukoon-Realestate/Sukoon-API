'use client';
import { useEffect, useState } from 'react';
import { fetchPolicyStatus, type PolicyStatus as Status } from '@/lib/api/chatPolicy';
export function PolicyStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    fetchPolicyStatus().then(value => { if (current) { setStatus(value); setFailed(false); } }).catch(() => { if (current) setFailed(true); });
    return () => { current = false; };
  }, [revision]);
  return <aside className="border rounded-xl p-4 m-4 space-y-2" aria-label="حالة تحليل المحادثات">
    <h2 className="font-bold">حالة الخدمة</h2>
    {failed && <p role="alert">تعذر التحقق من الحالة الحالية.</p>}
    {status && <>
      <p>الوضع: <bdi>{status.mode}</bdi> — النموذج: <bdi>{status.model}</bdi></p>
      {!status.private_inputs_approved && <p>إرسال المحتوى الخاص للمزوّد غير مفعّل. لا يجري تحليل محادثات المستخدمين.</p>}
      <p>طلبات اليوم: {status.daily_requests} / {status.daily_limit} — رسائل في الانتظار: {status.pending.count}</p>
      <p>آخر تحليل ناجح: {status.last_success_at ? new Date(status.last_success_at).toLocaleString('ar-EG') : 'لا يوجد'}</p>
      {status.last_failure_code && <p>آخر عطل: <bdi>{status.last_failure_code}</bdi></p>}
      <p>مراجعات تجاوزت ٤٨ ساعة: {status.overdue_reviews}</p>
    </>}
    <button className="min-h-12 underline" onClick={() => setRevision(value => value + 1)}>تحديث الحالة</button>
  </aside>;
}
