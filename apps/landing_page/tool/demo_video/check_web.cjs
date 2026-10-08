const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium, webkit } = require('playwright');

const baseUrl = new URL(process.argv[2] || 'http://127.0.0.1:4177/');
const chromePath = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const playLabel = 'شغّل العرض';
const retryLabel = 'أعد تشغيل العرض';
const openLabel = 'افتح الفيديو في علامة تبويب جديدة';

async function openSite(page) {
  await page.addInitScript(() => {
    window.sokounPlayGestures = [];
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function (...args) {
      if (this.id === 'sokoun-demo-video') window.sokounPlayGestures.push(navigator.userActivation.isActive);
      return play.apply(this, args);
    };
    window.addEventListener('flutter-first-frame', () => {
      window.sokounFirstFrameMs = performance.now();
    }, { once: true });
  });
  await page.goto(baseUrl.href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof window.sokounFirstFrameMs === 'number');
}

async function openDemo(page) {
  await enableSemantics(page);
  await clickControl(page, page.getByRole('button', { name: 'شوف التطبيق من جوه', exact: true }));
}

async function waitForPlayback(page) {
  await page.waitForFunction(() => {
    const video = document.querySelector('#sokoun-demo-video');
    return video && !video.paused && video.currentTime > 0.8;
  });
}

async function enableSemantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  await placeholder.waitFor({ state: 'attached' });
  // Enable Flutter's accessibility tree; all subsequent controls receive real
  // mouse events rather than synthetic DOM clicks.
  await placeholder.evaluate(node => node.click());
}

async function clickControl(page, control) {
  await control.waitFor({ state: 'attached' });
  for (let attempt = 0; attempt < 8; attempt++) {
    const box = await control.boundingBox();
    assert(box, 'The control must have a browser hit target.');
    const center = box.y + box.height / 2;
    const height = page.viewportSize().height;
    if (center > 90 && center < height - 40) {
      await control.click({ force: true });
      return;
    }
    await page.mouse.move(page.viewportSize().width / 2, height / 2);
    await page.mouse.wheel(0, center - height / 2);
    await page.waitForTimeout(120);
  }
  throw new Error('Could not bring the control into the Flutter viewport.');
}

async function checkPlayback(browser, engine, width) {
  const page = await browser.newPage({
    viewport: { width, height: width < 680 ? 844 : 1000 },
    reducedMotion: 'reduce',
  });
  page.setDefaultTimeout(30000);
  const errors = [];
  const mediaRequests = [];
  const externalRequests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname.endsWith('sokoun_demo.mp4')) mediaRequests.push(request);
    if (url.protocol.startsWith('http') && url.origin !== baseUrl.origin) externalRequests.push(url.href);
  });
  // Startup must succeed even if Google resources are blocked/unreachable.
  await page.route(/https:\/\/[^/]*(gstatic\.com|googleapis\.com)\//, route => route.abort());
  try {
    await openSite(page);
    assert.equal(await page.locator('#sokoun-loading').count(), 0, 'Remove the loading shell at the first frame.');
    const startup = await page.evaluate(() => ({
      firstFrameMs: Math.round(window.sokounFirstFrameMs),
      resources: performance.getEntriesByType('resource').map(entry => entry.name),
    }));
    assert(!startup.resources.some(url => /FlutterIconsax|riyal\.ttf/.test(url)), 'Do not load unused mobile fonts.');
    assert.equal(externalRequests.length, 0, 'Startup must use only the site origin.');
    assert.equal(mediaRequests.length, 0, 'Do not load the MP4 at startup.');
    await openDemo(page);
    assert.equal(mediaRequests.length, 0, 'Scrolling to the preview must not load the MP4.');
    const video = page.locator('#sokoun-demo-video');
    await video.waitFor({ state: 'attached' });
    assert(await video.evaluate(element => element.isConnected && element.preload === 'none' && element.controls));
    const directLink = page.getByRole('link', { name: openLabel, exact: true });
    assert.equal(await directLink.getAttribute('target'), '_blank');
    assert((await directLink.getAttribute('href')).endsWith('/assets/assets/videos/sokoun_demo.mp4'));
    await clickControl(page, page.getByRole('button', { name: playLabel, exact: true }));
    await waitForPlayback(page);
    assert.equal(await page.evaluate(() => window.sokounPlayGestures[0]), true, 'Call play during the trusted click.');
    const media = await video.evaluate(element => ({ duration: element.duration, width: element.videoWidth, height: element.videoHeight, muted: element.muted }));
    assert.equal(media.duration, 40);
    assert.equal(media.width, 1280);
    assert.equal(media.height, 720);
    assert.equal(media.muted, true);
    console.log(`${engine} ${width}: playback started (${startup.firstFrameMs} ms to first frame).`);

    // Reveal and click the native pause control. Chrome and WebKit use
    // different control bars. Seeking verifies the browser's byte ranges.
    const videoBox = await video.boundingBox();
    const pauseX = videoBox.x + (engine === 'chromium' ? 24 : width < 680 ? 28 : 56);
    const pauseY = videoBox.y + videoBox.height - (engine === 'chromium' ? 48 : 22);
    await page.mouse.move(pauseX, pauseY);
    await page.waitForTimeout(150);
    await page.mouse.click(pauseX, pauseY);
    await page.waitForFunction(() => document.querySelector('video')?.paused);
    await video.evaluate(element => { element.currentTime = 16; });
    await page.waitForFunction(() => {
      const video = document.querySelector('video');
      return video.currentTime > 10 && video.currentTime < 22;
    });
    await clickControl(page, page.getByRole('button', { name: playLabel, exact: true }));
    const seekPosition = await video.evaluate(element => element.currentTime);
    await page.waitForFunction(position => {
      const video = document.querySelector('video');
      return !video.paused && video.currentTime > position + 0.5;
    }, seekPosition);

    await video.evaluate(element => { element.currentTime = element.duration - 0.3; });
    await page.getByRole('button', { name: 'شغّل العرض من البداية', exact: true }).waitFor({ state: 'visible' });
    await clickControl(page, page.getByRole('button', { name: 'شغّل العرض من البداية', exact: true }));
    await page.waitForFunction(() => {
      const video = document.querySelector('video');
      return !video.paused && video.currentTime < 5;
    });
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ engine, viewportWidth: width, ...media, firstFrameMs: startup.firstFrameMs, externalStartupRequests: externalRequests.length, playback: 'play pause seek resume replay passed' }));
  } catch (error) {
    await page.screenshot({ path: `/tmp/sokoun-release-${engine}-${width}-failure.png` }).catch(() => {});
    throw error;
  } finally {
    await page.close();
  }
}

async function checkSlowAndFailedLoads(browser, scenario) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  page.setDefaultTimeout(30000);
  const errors = [];
  const mediaRequests = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route(/sokoun_demo\.mp4(?:\?|$)/, async route => {
    const url = new URL(route.request().url());
    mediaRequests.push(url);
    if (url.searchParams.has('retry')) return route.continue();
    if (scenario === 'stalled') return; // Leave the first response pending.
    if (scenario === 'failed') return route.fulfill({ status: 404, body: 'Missing video' });
    await new Promise(resolve => setTimeout(resolve, 6500));
    return route.continue();
  });
  try {
    await openSite(page);
    await openDemo(page);
    await clickControl(page, page.getByRole('button', { name: playLabel, exact: true }));
    assert.equal(await page.evaluate(() => window.sokounPlayGestures[0]), true);
    if (scenario !== 'slow') {
      await page.getByRole('button', { name: retryLabel, exact: true }).waitFor({ state: 'visible' });
      await page.getByRole('link', { name: openLabel, exact: true }).waitFor({ state: 'visible' });
      await clickControl(page, page.getByRole('button', { name: retryLabel, exact: true }));
    }
    await waitForPlayback(page);
    if (scenario !== 'slow') assert(mediaRequests.some(url => url.searchParams.has('retry')), 'Retry must make a fresh request.');
    assert.deepEqual(errors, []);
    console.log(`Chromium ${scenario} network: playback ${scenario === 'slow' ? 'preserves the play gesture' : 'recovers after retry'}.`);
  } catch (error) {
    await page.screenshot({ path: `/tmp/sokoun-native-${scenario}-failure.png` }).catch(() => {});
    throw error;
  } finally {
    await page.close();
  }
}

async function checkWithoutSemantics(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(30000);
  try {
    await openSite(page);
    await page.waitForTimeout(750);
    // The desktop header's app-preview action receives an ordinary mouse
    // click with normal motion and no Flutter accessibility tree enabled.
    await page.mouse.click(265, 34);
    // Flutter exposes platform-view semantics only after accessibility is
    // enabled. The ordinary pointer test targets the visible native button.
    const play = page.locator('#sokoun-demo-video + button');
    await page.waitForFunction(() => {
      const button = document.querySelector('#sokoun-demo-video')?.nextElementSibling;
      const rect = button?.getBoundingClientRect();
      return rect && rect.top > 90 && rect.bottom < innerHeight;
    });
    await play.click();
    await waitForPlayback(page);
    assert.equal(await page.evaluate(() => window.sokounPlayGestures[0]), true);
    console.log('Chromium ordinary mouse navigation and playback passed.');
  } catch (error) {
    await page.screenshot({ path: '/tmp/sokoun-native-pointer-failure.png' }).catch(() => {});
    throw error;
  } finally {
    await page.close();
  }
}

async function checkLegacyWorker(browser) {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  await context.route('**/flutter_service_worker.js', route => route.fulfill({
    contentType: 'application/javascript',
    // Model a real legacy worker that caches bootstrap as well as the app.
    // Moving migration after that script loads would leave users on old code.
    body: "self.addEventListener('install', () => self.skipWaiting()); self.addEventListener('activate', event => event.waitUntil(self.clients.claim())); self.addEventListener('fetch', event => { if (new URL(event.request.url).pathname.endsWith('/flutter_bootstrap.js')) event.respondWith(Promise.resolve(new Response('window.sokounStaleBootstrap = true;', { headers: { 'Content-Type': 'application/javascript' } }))); });",
  }));
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  try {
    await page.goto(baseUrl.href);
    await page.locator('flt-semantics-placeholder').waitFor({ state: 'attached' });
    await page.evaluate(async () => {
      await navigator.serviceWorker.register(new URL('flutter_service_worker.js', document.baseURI));
      await navigator.serviceWorker.ready;
    });
    await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
    await page.reload();
    await page.waitForFunction(async () => {
      const registration = await navigator.serviceWorker.getRegistration(document.baseURI);
      return !registration && !navigator.serviceWorker.controller && !document.getElementById('sokoun-loading');
    });
    assert.equal(await page.evaluate(() => window.sokounStaleBootstrap === true), false, 'Do not execute a cached obsolete bootstrap.');
    console.log('Legacy Flutter worker with cached bootstrap migration passed.');
  } finally {
    await context.close();
  }
}

(async () => {
  for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const browser = await type.launch({
      headless: true,
      ...(engine === 'chromium' && fs.existsSync(chromePath) ? { executablePath: chromePath } : {}),
    });
    try {
      for (const width of [1440, 390]) await checkPlayback(browser, engine, width);
      if (engine === 'chromium') {
        await checkWithoutSemantics(browser);
        for (const scenario of ['slow', 'failed', 'stalled']) await checkSlowAndFailedLoads(browser, scenario);
        await checkLegacyWorker(browser);
      }
    } finally {
      await browser.close();
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
