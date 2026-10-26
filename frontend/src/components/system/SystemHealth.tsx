'use client';

import React, { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { fetchSystemHealth } from '../../lib/api/system';
import { ApiError } from '../../lib/api/client';
import type { SystemHealth } from '../../lib/api/types';

const panel = 'min-w-0 space-y-3 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 sm:p-5';
const unavailable = 'غير متاح';
const seconds = (value: number | null | undefined) => value == null ? unavailable : `${Math.round(value)} ثانية`;
const millis = (value: number | null | undefined) => value == null ? unavailable : `${value.toLocaleString('ar-EG', { maximumFractionDigits: 1 })} مللي ثانية`;
const date = (value: string | number | null | undefined) => value == null ? unavailable : new Date(value).toLocaleString('ar-EG');
const stateLabels: Record<string, string> = { measured: 'قياسات متاحة', no_samples: 'لا توجد طلبات مسجلة في النافذة', unavailable, disabled: 'غير مفعّل' };
const incidentLabels: Record<string, string> = {
  'runtime.telemetry': 'تعذر جمع القياسات', 'runtime.api_errors': 'أخطاء الاستجابة',
  'runtime.api_latency': 'زمن الاستجابة', 'runtime.memory': 'استخدام الذاكرة',
  'runtime.scheduler': 'تشغيل المهام المجدولة', 'runtime.queue_backlog': 'تراكم الطابور',
  'runtime.queue_delay': 'تأخر المهام',
};

export function SystemHealthReadings({ data }: { data: SystemHealth }) {
  const t = data.telemetry;
  const incidents = data.incidents ?? [];
  const windowLabel = t ? `خلال نافذة القياس: ${seconds(t.window_seconds)}` : 'فترة القياس غير متاحة';
  const database = data.metrics.dbStatus === 'Reachable' ? 'الاتصال متاح' : 'الاتصال غير مؤكد';
  return <>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {[
        ['التوفر التاريخي', unavailable, 'لا يتوفر قياس تاريخي لنسبة التوفر.'],
        ['متوسط استجابة API', millis(t?.average_ms), windowLabel],
        ['أخطاء الخادم 5xx', t?.server_errors ?? unavailable, windowLabel],
        ['قاعدة البيانات', database, `وقت فحص الاتصال: ${date(data.metrics.dbSub)}`],
      ].map(([label, value, description]) => <dl className={panel} key={label}>
        <dt className="font-semibold">{label}</dt><dd className="text-2xl font-bold">{value}</dd>
        <dd className="text-sm text-[var(--text-muted)]">{description}</dd>
      </dl>)}
    </div>
    {t && <section className={panel} aria-label="القياسات المسجلة">
      <h2 className="font-bold">القياسات المسجلة</h2>
      <p>الحالة: {stateLabels[t.state] ?? unavailable} · {windowLabel}</p>
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div><dt>عدد الطلبات</dt><dd>{t.requests ?? unavailable}</dd></div>
        <div><dt>نسبة أخطاء الخادم</dt><dd>{t.error_rate == null ? unavailable : `${(t.error_rate * 100).toLocaleString('ar-EG', { maximumFractionDigits: 2 })}%`}</dd></div>
        <div><dt>زمن 95٪ من الطلبات (p95)</dt><dd>{t.p95_upper_ms != null ? `حتى ${millis(t.p95_upper_ms)}`
          : t.p95_lower_ms != null ? `يتجاوز ${millis(t.p95_lower_ms)}` : unavailable}</dd></div>
        <div><dt>ذاكرة الحاوية</dt><dd>{t.memory.ratio == null ? unavailable : `${(t.memory.ratio * 100).toLocaleString('ar-EG', { maximumFractionDigits: 1 })}%`}</dd></div>
        <div><dt>المهام المنتظرة</dt><dd>{t.queue?.pending ?? unavailable} · {stateLabels[t.queue?.state ?? 'unavailable'] ?? unavailable}</dd></div>
        <div><dt>عمر أقدم مهمة</dt><dd>{seconds(t.queue?.oldest_seconds)}</dd></div>
      </dl>
      <p>تشغيل العمال والجدولة: {t.runtime == null ? 'غير مؤكد' : t.runtime.failures.length ? 'توجد حالات تحتاج متابعة' : 'لم تُرصد أعطال في هذه القراءة'}</p>
      {!!t.runtime?.failures.length && <ul className="list-inside list-disc">{t.runtime.failures.map(code => <li key={code} dir="ltr">{code}</li>)}</ul>}
      <p className="text-sm">إصدار الخدمة: <bdi>{t.release_sha || unavailable}</bdi></p>
    </section>}
    <section className={panel} aria-label="التنبيهات التشغيلية">
      <h2 className="font-bold">التنبيهات التشغيلية المسجلة</h2>
      <p className="text-sm text-[var(--text-muted)]">القياس المفقود لا يثبت استعادة الخدمة. الحالات المفتوحة تظل بحاجة إلى متابعة.</p>
      {!incidents.length ? <p>لا توجد تنبيهات مسجلة.</p> : <ul className="space-y-4">{incidents.map(item => <li key={item.code}>
        <p className="font-semibold">{incidentLabels[item.code] ?? item.code} — {item.state === 'open' ? 'مفتوح' : 'تمت الاستعادة'}</p>
        <p>مرات الحدوث: {item.occurrences} · بدأ: {date(item.opened_at)}{item.resolved_at && ` · تمت الاستعادة: ${date(item.resolved_at)}`}</p>
      </li>)}</ul>}
    </section>
    <section className={panel} aria-label="أداء المسارات">
      <h2 className="font-bold">أداء مسارات API</h2><p>{windowLabel}</p>
      {!t?.routes.length ? <p>لا تتوفر قياسات للمسارات في هذه القراءة.</p> : <ul className="grid gap-4 lg:grid-cols-2">{t.routes.map(row => <li key={row.route} className="min-w-0 rounded-lg border border-[var(--divider)] p-3">
        <p dir="ltr" className="break-all font-mono text-sm">{row.route}</p>
        <p>الطلبات: {row.requests} · أخطاء 5xx: {row.errors}</p>
        <p>متوسط الاستجابة: {row.requests ? millis(row.duration_ms / row.requests) : unavailable}</p>
      </li>)}</ul>}
    </section>
    <section className={panel} aria-label="سجل التدقيق">
      <h2 className="font-bold">أحدث عمليات الإدارة</h2>
      {!data.auditLogs.length ? <p>لا توجد عمليات مسجلة.</p> : <ul className="divide-y divide-[var(--divider)]">{data.auditLogs.slice(0, 6).map(log => <li key={log.id} className="space-y-1 py-3">
        <p className="font-semibold">{log.typeBadge} · {log.action}</p>
        <p>{log.operator} · {log.time}</p><p className="text-sm">{log.target}</p>
      </li>)}</ul>}
    </section>
  </>;
}

type Result = { key: number; data: SystemHealth | null; error: string };
export default function SystemHealthPage() {
  const [refresh, setRefresh] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const busy = result?.key !== refresh;
  const data = result?.data;
  useEffect(() => {
    const controller = new AbortController();
    const token = localStorage.getItem('sukoon_access_token');
    void fetchSystemHealth(controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ key: refresh, data, error: '' });
    }).catch(error => {
      if (controller.signal.aborted) return;
      const denied = (error instanceof ApiError && [401, 403].includes(error.status)) || localStorage.getItem('sukoon_access_token') !== token;
      setResult(previous => ({ key: refresh, data: denied ? null : previous?.data ?? null,
        error: denied ? 'لم تعد هذه القراءة متاحة لهذه الجلسة أو الصلاحية.' : 'تعذر تحديث القياسات. أعد المحاولة.' }));
    });
    return () => controller.abort();
  }, [refresh]);

  return <div dir="rtl" className="min-w-0 flex-1 pb-12 [overflow-wrap:anywhere]">
    <Header title="صحة النظام وسجل التدقيق" subtitle="القياسات المسجلة وحالة المهام وعمليات الإدارة"
      lastUpdated={data?.telemetry ? date(data.telemetry.measured_at * 1000) : 'لم تكتمل القراءة'} />
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8" aria-busy={busy}>
      <button type="button" className="min-h-12 rounded-xl border px-4 py-3 disabled:opacity-50" disabled={busy} onClick={() => setRefresh(value => value + 1)}>
        {busy ? 'جارٍ تحديث القياسات…' : 'تحديث القياسات'}
      </button>
      {!busy && result?.error && <p role="alert">{result.error}{data && ' البيانات الظاهرة تخص آخر قراءة ناجحة، وليست نتيجة التحديث الحالي.'}</p>}
      {busy && data && <p role="status">البيانات الظاهرة تخص آخر قراءة ناجحة حتى اكتمال التحديث.</p>}
      {data && <SystemHealthReadings data={data} />}
    </main>
  </div>;
}
