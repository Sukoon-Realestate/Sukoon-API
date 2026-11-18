// Local browser acceptance with synthetic server responses. No hosted commands.
// Supply SUKOON_PLAYWRIGHT_MODULE when Playwright is installed outside this app.
const { chromium, expect } = require(process.env.SUKOON_PLAYWRIGHT_MODULE || 'playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const origin = process.env.SUKOON_QA_ORIGIN || 'http://127.0.0.1:3022';
const output = process.env.SUKOON_QA_OUTPUT || '/private/tmp/sprint2-browser';
assert.ok(['127.0.0.1', 'localhost'].includes(new URL(origin).hostname), 'Use a disposable loopback app');
const paths = ['/', '/system/logs', '/roles', '/support', '/properties/review', '/settings', '/security'];
const results = [];
let browser;
async function scenario(name, run) {
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1366, height: 900 }, timezoneId: 'Africa/Cairo' });
  let profile = { id: 'qa-owner', name: 'QA owner', email: 'owner@example.invalid', role: 'system_owner', canManageStaff: true, allowedPaths: paths };
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await context.addInitScript(() => {
    if (window.top !== window) return;
    localStorage.setItem('sukoon_admin_mode', 'live');
    localStorage.setItem('sukoon_access_token', 'synthetic-browser-token');
  });
  const respond = (route, data, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify({ message: status < 400 ? 'OK' : 'Controlled failure', data }) });
  let handler = async () => false;
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (!url.pathname.startsWith('/api/')) return route.continue();
    if (url.pathname === '/api/v1/admin/session/') return respond(route, profile);
    if (url.pathname === '/api/v1/admin/followups/') return respond(route, { measured_at: '2026-11-17T12:00:00Z', results: [] });
    try {
      if (await handler(route, url, respond)) return;
      throw new Error(`Unhandled fixture request ${route.request().method()} ${url.pathname}`);
    } catch (error) { errors.push(error.message); await route.abort().catch(() => {}); }
  });
  try {
    await run({ page, context, respond, setHandler: value => { handler = value; }, setProfile: value => { profile = value; } });
    assert.deepEqual(errors, [], 'No browser application exceptions');
    await page.screenshot({ path: path.join(output, name + '.png'), fullPage: true });
    results.push({ name, passed: true });
    console.log('PASS', name);
  } catch (error) {
    await page.screenshot({ path: path.join(output, name + '-failure.png'), fullPage: true });
    results.push({ name, passed: false, error: error.message });
    throw error;
  } finally { await context.close(); }
}
const auditRow = (id, action) => ({ id, action, time: '2026-11-17 12:00', typeBadge: 'نظام', target: '=1+1', operator: 'مراجع، "اختبار"' });
const auditPage = (rows, page = 1, count = rows.length) => ({ results: rows, count, page, per_page: 1, total_pages: Math.max(1, count), next: page < count ? `?page=${page + 1}` : null, previous: page > 1 ? `?page=${page - 1}` : null });
async function main() {
  await fs.mkdir(output, { recursive: true });
  browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  await scenario('audit-failure-retry-download', async ({ page, setHandler }) => {
    let fail = true;
    setHandler(async (route, url, respond) => {
      assert.equal(url.pathname, '/api/v1/admin/system/logs/');
      const current = Number(url.searchParams.get('page') || 1);
      await respond(route, fail ? null : auditPage([auditRow(`row-${current}`, `قرار عربي ${current}`)], current, 2), fail ? 503 : 200);
      return true;
    });
    const response = await page.goto(origin + '/admin/system/logs');
    assert.equal(response.headers()['content-security-policy'], "frame-ancestors 'none'");
    assert.equal(response.headers()['x-frame-options'], 'DENY');
    await expect(page.locator('[role=alert]:not(#__next-route-announcer__)')).toContainText('تعذر تحميل سجل النشاط');
    await expect(page.getByText('لا توجد سجلات مطابقة', { exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'تصدير الصفحة CSV' })).toBeDisabled();
    fail = false;
    await page.getByRole('button', { name: 'إعادة المحاولة', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'قرار عربي 1', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'الصفحة 2', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'قرار عربي 2', exact: true })).toBeVisible();
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: 'تصدير الصفحة CSV' }).click();
    const download = await downloadEvent;
    assert.equal(download.suggestedFilename(), 'audit-logs-page-2.csv');
    const csvPath = path.join(output, download.suggestedFilename());
    await download.saveAs(csvPath);
    const csv = await fs.readFile(csvPath, 'utf8');
    assert.ok(csv.startsWith('\uFEFF'));
    assert.ok(csv.includes('قرار عربي 2') && !csv.includes('قرار عربي 1'));
    assert.ok(csv.includes('"\'=1+1"'));
    assert.ok(csv.includes('"مراجع، ""اختبار"""'));
  });
  await scenario('audit-filters-discard-late-result', async ({ page, setHandler }) => {
    let release;
    let started;
    const oldStarted = new Promise(resolve => { started = resolve; });
    setHandler(async (route, url, respond) => {
      const search = url.searchParams.get('search') || '';
      if (search === 'old') { started(); await new Promise(resolve => { release = resolve; }); }
      await respond(route, search === 'empty' ? auditPage([]) : auditPage([auditRow(search || 'first', search || 'initial result')]));
      return true;
    });
    await page.goto(origin + '/admin/system/logs');
    await expect(page.getByRole('cell', { name: 'initial result', exact: true })).toBeVisible();
    const search = page.getByPlaceholder('بحث في السجل...');
    await search.fill('old'); await oldStarted;
    await expect(page.getByRole('cell', { name: 'initial result', exact: true })).toHaveCount(0);
    await search.fill('new');
    await expect(page.getByRole('cell', { name: 'new', exact: true })).toBeVisible();
    release();
    await expect(page.getByRole('cell', { name: 'old', exact: true })).toHaveCount(0);
    await search.fill('empty');
    await expect(page.getByText('لا توجد سجلات مطابقة', { exact: true })).toBeVisible();
    await expect(page.locator('[role=alert]:not(#__next-route-announcer__)')).toHaveCount(0);
  });
  await scenario('support-role-command-and-recovery', async ({ page, setHandler, setProfile }) => {
    setProfile({ id: 'qa-support', name: 'QA support', email: 'support@example.invalid', role: 'support', canManageStaff: false, allowedPaths: ['/', '/support', '/security'] });
    let revision = 7;
    let commands = 0;
    let receiptKey;
    const ticket = () => ({ id: 'ticket-1', reference: 'QA-1', subject: 'استفسار الاختبار', user: 'مستخدم اصطناعي', workspace: 'tenant', status: 'مفتوح', revision, assignedTo: 'QA support', actions: { reply: true, note: true, claim: false }, messages: [{ id: 'message-1', sender: 'user', body: 'رسالة اختبار محفوظة', created_at: '2026-11-17T12:00:00Z', attachments: [] }], internal_notes: [], transitions: [] });
    setHandler(async (route, url, respond) => {
      if (url.pathname === '/api/v1/admin/support/team/') await respond(route, { results: [{ id: 'qa-support', name: 'QA support' }] });
      else if (url.pathname.includes('/receipts/')) {
        assert.ok(url.pathname.includes(receiptKey));
        await respond(route, { status: 'confirmed' });
      } else if (url.pathname === '/api/v1/admin/support/ticket-1/') {
        if (route.request().method() === 'POST') {
          const body = route.request().postDataJSON();
          assert.equal(body.expected_revision, 7);
          assert.equal(body.body, 'رد الاختبار');
          assert.equal(body.action, 'reply');
          receiptKey = route.request().headers()['idempotency-key'];
          assert.ok(receiptKey);
          commands++; revision++;
          // The server committed but the acknowledgment was lost.
          await respond(route, null, 503);
        } else await respond(route, ticket());
      } else return false;
      return true;
    });
    await page.goto(origin + '/admin/support/ticket-1');
    await expect(page.getByText('رسالة اختبار محفوظة', { exact: true })).toBeVisible();
    await page.getByLabel('الرد للمستخدم', { exact: true }).fill('رد الاختبار');
    await page.getByRole('button', { name: 'إرسال الرد', exact: true }).click();
    await expect(page.getByRole('button', { name: 'إرسال الرد', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'استعادة نتيجة العملية الأصلية', exact: true }).click();
    await expect(page.getByText('استُعيد إيصال العملية المحفوظة.', { exact: true })).toBeVisible();
    assert.equal(commands, 1);
    await page.goto(origin + '/admin/settings');
    await expect(page.getByText('هذا القسم غير متاح لصلاحيات حسابك الحالية.', { exact: true })).toBeVisible();
  });
  await scenario('property-review-stale-version-recovery', async ({ page, setHandler, setProfile }) => {
    setProfile({ id: 'qa-reviewer', name: 'QA reviewer', email: 'reviewer@example.invalid', role: 'property_reviewer', canManageStaff: false, allowedPaths: ['/', '/properties/review', '/security'] });
    let current = 3;
    let writes = 0;
    const detail = () => ({ id: 'property-1', title: 'عقار الاختبار', review_revision: current, review_version: `version-${current}`, review_snapshot: {}, moderation_blocked: false, status: 'قيد المراجعة', description: 'نسخة محفوظة للمراجعة', images: [], actions: { approve: { enabled: true } }, review_history: [] });
    setHandler(async (route, url, respond) => {
      if (url.pathname === '/api/v1/admin/properties/') await respond(route, { results: [{ id: 'property-1', title: 'عقار الاختبار', status: 'قيد المراجعة' }], count: 1, next: null, previous: null });
      else if (url.pathname === '/api/v1/admin/properties/property-1/') await respond(route, detail());
      else if (url.pathname.endsWith('/approve/')) {
        assert.equal(route.request().postDataJSON().expected_version, 'version-3');
        writes++; current = 4; await respond(route, null, 409);
      } else if (url.pathname.includes('/receipts/')) await respond(route, { status: 'absent_final' });
      else return false;
      return true;
    });
    await page.goto(origin + '/admin/properties/review?id=property-1');
    await expect(page.getByText('الإصدار 3', { exact: false })).toBeVisible();
    await page.getByRole('button', { name: 'تأكيد اعتماد العقار', exact: true }).click();
    await expect(page.getByRole('button', { name: 'تأكيد اعتماد العقار', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'استعادة نتيجة القرار', exact: true }).click();
    await expect(page.getByText('الإصدار 4', { exact: false })).toBeVisible();
    await expect(page.getByText('لم يُنفذ القرار السابق. راجع النسخة الحالية قبل اتخاذ قرار جديد.', { exact: true })).toBeVisible();
    assert.equal(writes, 1);
  });
  await scenario('owner-catalog-conflict-and-save', async ({ page, setHandler }) => {
    let revision = 2;
    let writes = 0;
    const item = () => ({ id: 'page-1', revision, values: { title_ar: `عنوان النسخة ${revision}` } });
    setHandler(async (route, url, respond) => {
      if (url.pathname === '/api/v1/admin/content/') await respond(route, { can_edit: true, blocking_reason: '', catalogs: [{ kind: 'pages', label: 'صفحات الاختبار', fields: [{ name: 'title_ar', label: 'عنوان الصفحة', type: 'text', required: true, fixed: false, max_length: 100, choices: [] }] }] });
      else if (url.pathname === '/api/v1/admin/content/pages/') await respond(route, { results: [item()], page: 1, total_pages: 1, count: 1 });
      else if (url.pathname === '/api/v1/admin/content/pages/page-1/') {
        if (route.request().method() === 'POST') {
          writes++;
          const body = route.request().postDataJSON();
          assert.equal(body.expected_revision, writes === 1 ? 2 : 3);
          assert.ok(route.request().headers()['idempotency-key']);
          revision++;
          await respond(route, writes === 1 ? null : item(), writes === 1 ? 409 : 200);
        } else await respond(route, item());
      } else return false;
      return true;
    });
    page.on('dialog', dialog => dialog.accept());
    await page.goto(origin + '/admin/settings');
    await expect(page.getByLabel('عنوان الصفحة', { exact: true })).toHaveValue('عنوان النسخة 2');
    await page.getByLabel('عنوان الصفحة', { exact: true }).fill('تعديل أول');
    await page.getByLabel('سبب التغيير', { exact: true }).fill('تحقق من تعارض النسخة');
    await page.getByRole('button', { name: 'حفظ المحتوى', exact: true }).click();
    await expect(page.locator('[role=alert]:not(#__next-route-announcer__)')).toBeVisible();
    await expect(page.getByText('تم حفظ المحتوى وإصداره.', { exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'تحديث القائمة', exact: true }).click();
    await expect(page.getByLabel('عنوان الصفحة', { exact: true })).toHaveValue('عنوان النسخة 3');
    await page.getByLabel('عنوان الصفحة', { exact: true }).fill('تعديل ثان');
    await page.getByLabel('سبب التغيير', { exact: true }).fill('حفظ النسخة الحالية');
    await page.getByRole('button', { name: 'حفظ المحتوى', exact: true }).click();
    await expect(page.getByText('تم حفظ المحتوى وإصداره.', { exact: true })).toBeVisible();
    await expect(page.getByLabel('عنوان الصفحة', { exact: true })).toHaveValue('عنوان النسخة 4');
    assert.equal(writes, 2);
  });
  await scenario('permissions-read-only-and-framing-blocked', async ({ page, context, setHandler }) => {
    setHandler(async (route, url, respond) => {
      if (url.pathname === '/api/v1/admin/staff/') await respond(route, { results: [], count: 0, next: null, previous: null });
      else if (url.pathname === '/api/v1/admin/staff/roles/') await respond(route, []);
      else if (url.pathname === '/api/v1/admin/permissions/') await respond(route, [{ id: 'review', action: 'مراجعة الاختبار', systemOwner: true, mainAdmin: false }]);
      else return false;
      return true;
    });
    await page.goto(origin + '/admin/roles');
    await expect(page.getByText('مصفوفة الصلاحيات (للعرض فقط)', { exact: true })).toBeVisible();
    await expect(page.getByText('انقر للتعديل المباشر', { exact: false })).toHaveCount(0);
    // Even same-origin parents must not embed authenticated administration.
    await context.route(origin + '/qa-framing-parent', route => route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Framing probe</title><iframe src="/admin/roles"></iframe>' }));
    const blocked = page.waitForEvent('console', { predicate: message => /frame-ancestors|X-Frame-Options/i.test(message.text()), timeout: 10000 });
    await page.goto(origin + '/qa-framing-parent');
    await blocked;
    assert.equal(page.frames().filter(frame => /\/admin\/roles$/.test(frame.url())).length, 0, 'Chrome blocked the admin document');
  });
}
main().catch(error => { console.error(error); process.exitCode = 1; }).finally(async () => {
  await fs.writeFile(path.join(output, 'results.json'), JSON.stringify({ origin, transport: 'synthetic intercepted API', results }, null, 2) + '\n');
  await browser?.close();
});
