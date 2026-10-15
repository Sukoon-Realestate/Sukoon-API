/* Same-origin admin preview. No account token or URL-borne bootstrap. */
document.querySelector('#tour-preview').addEventListener('click', async () => {
  const output = document.querySelector('#tour-preview-status');
  const form = document.querySelector('#tour-review');
  const popup = window.open('about:blank', '_blank');
  if (!popup) { output.textContent = 'Allow a popup to inspect this package.'; return; }
  try {
    const body = new FormData(form); body.set('action', 'preview');
    const response = await fetch(location.pathname, { method: 'POST', body, credentials: 'same-origin', cache: 'no-store' });
    const session = await response.json();
    if (!response.ok) throw new Error(session.error || 'Preview unavailable');
    const url = new URL(session.viewer_url);
    if (url.origin !== location.origin || url.protocol !== 'https:' || url.pathname !== '/tours/' || url.search || url.hash) throw new Error('Serve the viewer on the same HTTPS origin as this review console.');
    popup.location = url.href;
    const started = Date.now(); let initialized = false;
    const interval = setInterval(() => {
      if (popup.closed || Date.now() - started > 55000) { clearInterval(interval); output.textContent = 'Preview closed or timed out.'; return; }
      try {
        if (popup.location.href !== url.href || !popup.sokounTour) return;
        popup.SokounTour = { postMessage(raw) {
          if (raw.length > 16384) return;
          const message = JSON.parse(raw);
          if (initialized) {
            if (message.type === 'requestClose' && message.session_id === session.session_id) popup.close();
            return;
          }
          if (message.protocol_version !== 1 || message.type !== 'viewerReady' || typeof message.viewer_instance_id !== 'string') return;
          initialized = true;
          popup.sokounTour.receive({ protocol_version: 1, type: 'initialize', message_id: crypto.randomUUID(),
            viewer_instance_id: message.viewer_instance_id, session_id: session.session_id,
            payload: { session_id: session.session_id, bootstrap_token: session.bootstrap_token, language: document.documentElement.lang.startsWith('ar') ? 'ar' : 'en', reduced_motion: matchMedia('(prefers-reduced-motion: reduce)').matches } });
          session.bootstrap_token = ''; clearInterval(interval); output.textContent = 'Private preview opened. Inspect this package before deciding.';
        } };
        popup.sokounTour.ready();
      } catch { clearInterval(interval); output.textContent = 'The preview changed origin. Close it and check deployment configuration.'; }
    }, 100);
  } catch (error) { popup.close(); output.textContent = error.message || 'Preview failed.'; }
});
