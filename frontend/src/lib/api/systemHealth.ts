import type { SystemHealth } from './types';

const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value: unknown) => typeof value === 'string';
const count = (value: unknown) => Number.isSafeInteger(value) && (value as number) >= 0;
const number = (value: unknown) => typeof value === 'number' && Number.isFinite(value) && value >= 0;
const optionalNumber = (value: unknown) => value === null || number(value);
const optionalCount = (value: unknown) => value === null || count(value);
const date = (value: unknown) => typeof value === 'string' && Number.isFinite(Date.parse(value));

/** Reject malformed measurements; missing observations are explicitly null. */
export function validateSystemHealth(value: unknown): asserts value is SystemHealth {
  const invalid = () => { throw new Error('Invalid system health response'); };
  if (!object(value)) return invalid();
  const { metrics, telemetry: t, incidents, auditLogs } = value;
  if (!object(metrics) || !['uptime', 'uptimeSub', 'responseTime', 'responseSub',
    'errorsToday', 'errorsSub', 'dbStatus', 'dbSub'].every(key => text(metrics[key])) || !date(metrics.dbSub)) return invalid();
  if (!object(t) || !['measured', 'no_samples', 'unavailable'].includes(String(t.state)) ||
      !number(t.measured_at) || !number(t.window_seconds) || t.window_seconds === 0 ||
      !['requests', 'server_errors'].every(key => optionalCount(t[key])) ||
      !['error_rate', 'average_ms', 'p95_upper_ms'].every(key => optionalNumber(t[key])) ||
      (t.p95_lower_ms !== undefined && !optionalNumber(t.p95_lower_ms)) || !text(t.release_sha)) return invalid();
  if (!object(t.memory) || !['ratio', 'used_bytes', 'limit_bytes'].every(key => optionalNumber((t.memory as Record<string, unknown>)[key])) || !text(t.memory.scope)) return invalid();
  if (t.runtime !== null && (!object(t.runtime) || !Array.isArray(t.runtime.failures) || !t.runtime.failures.every(text))) return invalid();
  if (t.queue !== undefined && (!object(t.queue) || !['disabled', 'unavailable', 'measured'].includes(String(t.queue.state)) ||
      !optionalCount(t.queue.pending) || !optionalNumber(t.queue.oldest_seconds))) return invalid();
  if (!Array.isArray(t.routes) || !t.routes.every(row => object(row) && text(row.route) &&
      count(row.requests) && count(row.errors) && number(row.duration_ms))) return invalid();
  if (!Array.isArray(incidents) || !incidents.every(row => object(row) && text(row.code) &&
      ['open', 'resolved'].includes(String(row.state)) && count(row.occurrences) &&
      (row.opened_at === null || date(row.opened_at)) && (row.resolved_at === null || date(row.resolved_at)))) return invalid();
  if (!Array.isArray(auditLogs) || !auditLogs.every(row => object(row) &&
      ['id', 'time', 'action', 'typeBadge', 'target', 'operator'].every(key => text(row[key])))) return invalid();
}
