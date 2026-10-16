(() => {
  const root = document.documentElement;
  const media = matchMedia('(prefers-color-scheme: dark)');
  const storageKey = 'sukoon-proposal-theme';
  const params = new URLSearchParams(location.search);
  let mode = params.get('theme');
  if (!['light', 'dark', 'system'].includes(mode)) {
    try { mode = localStorage.getItem(storageKey) || 'system'; } catch { mode = 'system'; }
  }
  if (!['light', 'dark', 'system'].includes(mode)) mode = 'system';
  let toastTimer;
  const toast = document.querySelector('.toast');
  function notify(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 4200);
  }
  function syncTheme() {
    const effective = mode === 'system' ? (media.matches ? 'dark' : 'light') : mode;
    root.dataset.theme = effective;
    root.dataset.mode = mode;
    document.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)));
    document.querySelectorAll('[data-theme-label]').forEach(el => {
      el.textContent = mode === 'system' ? `حسب الجهاز · ${effective === 'dark' ? 'داكن' : 'فاتح'}` : 'اختيار المظهر محفوظ';
    });
    document.querySelectorAll('a[href^="index.html"],a[href^="design-map.html"]').forEach(a => {
      const url = new URL(a.getAttribute('href'), location.href);
      url.searchParams.set('theme', mode);
      a.href = url.href;
    });
  }
  function setMode(value) {
    mode = value;
    try { localStorage.setItem(storageKey, value); } catch { /* Offline file storage may be unavailable. */ }
    try { const url = new URL(location.href); url.searchParams.set('theme', value); history.replaceState(null, '', url.href); } catch { /* Some file viewers disallow history changes. */ }
    syncTheme();
  }
  media.addEventListener('change', () => { if (mode === 'system') syncTheme(); });
  syncTheme();

  const focusDialog = document.querySelector('.focus-dialog');
  const focusBody = document.querySelector('.focus-body');
  let focusedScreen = 1;
  function showScreen(number) {
    number = Math.min(20, Math.max(1, Number(number)));
    const screen = document.querySelector(`#S${String(number).padStart(2, '0')}`);
    if (!screen) { location.href = `index.html?theme=${mode}#S${String(number).padStart(2, '0')}`; return; }
    focusedScreen = number;
    const clone = screen.querySelector('.phone').cloneNode(true);
    clone.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
    focusBody.replaceChildren(clone);
    document.querySelector('[data-focus-title]').textContent = screen.querySelector('.screen-head h2').textContent;
    document.querySelector('[data-focus-prev]').disabled = number === 1;
    document.querySelector('[data-focus-next]').disabled = number === 20;
    if (!focusDialog.open) focusDialog.showModal();
    focusBody.scrollTop = 0;
    syncTheme();
  }
  const decisionDialog = document.querySelector('.decision-dialog');
  let onConfirm = null;
  function decision(title, body, callback) {
    document.querySelector('#decision-title').textContent = title;
    document.querySelector('[data-decision-body]').textContent = body;
    document.querySelector('[data-decision-confirm]').textContent = 'تأكيد';
    onConfirm = callback;
    decisionDialog.showModal();
  }
  decisionDialog.addEventListener('close', () => { onConfirm = null; });

  document.querySelector('#group-filter')?.addEventListener('change', e => {
    document.querySelectorAll('.screen').forEach(s => { s.hidden = e.target.value !== 'all' && s.dataset.group !== e.target.value; });
  });
  document.addEventListener('input', e => {
    if (e.target.matches('.range')) {
      e.target.closest('.phone').querySelector('[data-price-output]').textContent = new Intl.NumberFormat('ar-EG').format(e.target.value) + ' ج.م';
    }
    if (e.target.matches('.otp-row input')) {
      e.target.value = e.target.value.replace(/[^0-9٠-٩]/g, '').slice(0, 1);
      if (e.target.value && e.target.nextElementSibling) e.target.nextElementSibling.focus();
    }
  });
  document.addEventListener('submit', e => {
    if (e.target.matches('.composer')) { e.preventDefault(); sendMessage(e.target.closest('.phone')); }
  });
  function sendMessage(phone) {
    const input = phone.querySelector('.composer input');
    const value = input.value.trim();
    if (!value) { input.focus(); return; }
    const bubble = document.createElement('div');
    bubble.className = 'bubble outgoing';
    bubble.textContent = value;
    const label = document.createElement('small');
    label.textContent = 'رسالة توضيحية · محفوظة في المعاينة فقط';
    bubble.append(label);
    const thread = phone.querySelector('.thread-scroll');
    thread.append(bubble);
    thread.scrollTop = thread.scrollHeight;
    input.value = '';
  }
  function applyRequestFilter(phone, tab) {
    phone.querySelectorAll('.request').forEach(r => { r.hidden = tab === '1' ? r.dataset.requestState !== 'pending' : tab === '2' ? r.dataset.requestState !== 'confirmed' : false; });
  }
  function updateRequest(button, accepted) {
    const request = button.closest('.request');
    if (!request) {
      const phone = button.closest('.phone');
      const label = phone.querySelector('.summary .badge');
      label.className = `badge ${accepted ? '' : 'error'}`;
      label.textContent = accepted ? 'مؤكدة' : 'مرفوضة';
      phone.querySelectorAll('.actions button').forEach(b => b.disabled = true);
      notify(accepted ? 'معاينة: تم قبول الطلب التوضيحي' : 'معاينة: تم رفض الطلب التوضيحي'); return;
    }
    request.dataset.requestState = accepted ? 'confirmed' : 'rejected';
    const label = request.querySelector('.badge');
    label.className = `badge ${accepted ? '' : 'error'}`;
    label.textContent = accepted ? 'مؤكدة' : 'مرفوضة';
    const feedback = document.createElement('div');
    feedback.className = 'request-status';
    feedback.textContent = accepted ? 'تم تأكيد موعد المعاينة' : 'تم رفض الطلب';
    request.querySelector('.request-actions')?.replaceWith(feedback);
    const phone = request.closest('.phone');
    const tab = phone.querySelector('[data-tabs=requests] [aria-pressed=true]');
    if (tab) applyRequestFilter(phone, tab.dataset.tab);
    notify('تم تحديث الطلب التوضيحي؛ لا يتم إرسال بيانات');
  }
  function emptyBlock(text) {
    const block = document.createElement('div');
    block.className = 'notice'; block.dataset.localEmpty = 'true'; block.textContent = text;
    return block;
  }
  document.addEventListener('click', e => {
    const button = e.target.closest('button');
    if (!button || button.disabled) return;
    if (button.dataset.mode) { setMode(button.dataset.mode); return; }
    if (button.hasAttribute('data-close-focus')) { focusDialog.close(); return; }
    if (button.hasAttribute('data-focus-prev')) { showScreen(focusedScreen - 1); return; }
    if (button.hasAttribute('data-focus-next')) { showScreen(focusedScreen + 1); return; }
    if (button.hasAttribute('data-decision-cancel')) { decisionDialog.close(); return; }
    if (button.hasAttribute('data-decision-confirm')) {
      const callback = onConfirm; onConfirm = null; decisionDialog.close(); callback?.(); return;
    }
    if (button.dataset.open) { showScreen(button.dataset.open); return; }
    if (button.dataset.go) { showScreen(button.dataset.go); return; }
    const phone = button.closest('.phone');
    const choice = button.closest('[data-choice]');
    if (choice) {
      const isMulti = choice.dataset.choice === 'multi';
      if (isMulti) button.setAttribute('aria-pressed', String(button.getAttribute('aria-pressed') !== 'true'));
      else choice.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      if (choice.dataset.choice === 'home-type') {
        const idx = [...choice.children].indexOf(button);
        const properties = phone.querySelectorAll('.property');
        phone.querySelector('[data-local-empty]')?.remove();
        properties.forEach((p,i) => { p.hidden = idx === 3 || (idx === 1 && i !== 0) || (idx === 2 && i !== 1); });
        if (idx === 3) properties[0].before(emptyBlock('لا توجد فيلا ضمن بيانات المعاينة. جرّب نوعًا آخر.'));
      }
      if (choice.dataset.choice === 'day') notify('اختيار يوم توضيحي؛ المواعيد الفعلية تُحمّل من الخادم عند التنفيذ');
      return;
    }
    const tabGroup = button.closest('[data-tabs]');
    if (tabGroup) {
      tabGroup.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      const tab = button.dataset.tab;
      if (tabGroup.dataset.tabs === 'requests') applyRequestFilter(phone, tab);
      if (tabGroup.dataset.tabs === 'properties') phone.querySelectorAll('.property').forEach((p,i) => { p.hidden = tab !== '0' && i !== Number(tab) - 1; });
      if (tabGroup.dataset.tabs === 'visits') {
        phone.querySelector('[data-local-empty]')?.remove();
        phone.querySelector('[data-visit-list]').hidden = tab === '1';
        if (tab === '1') tabGroup.after(emptyBlock('لسه مفيش معاينات سابقة في المعاينة التوضيحية.'));
      }
      return;
    }
    const action = button.dataset.action;
    if (action === 'save') {
      const saved = button.getAttribute('aria-pressed') !== 'true';
      button.setAttribute('aria-pressed', saved);
      button.setAttribute('aria-label', saved ? 'إزالة من المحفوظة' : 'حفظ العقار');
      if (phone.dataset.screen === '9' && !saved) {
        button.closest('.property').remove();
        phone.querySelector('.phone-scroll > p').textContent = `عدد العقارات المحفوظة: ${phone.querySelectorAll('.property').length}`;
        if (!phone.querySelector('.property')) phone.querySelector('.phone-scroll').append(emptyBlock('لسه مفيش عقارات محفوظة. استكشف العقارات واحفظ الأماكن اللي تناسبك.'));
      }
      notify(saved ? 'معاينة: تم حفظ العقار' : 'معاينة: تمت إزالة العقار'); return;
    }
    if (action === 'password') {
      const input = button.parentElement.querySelector('input');
      input.type = input.type === 'password' ? 'text' : 'password';
      button.setAttribute('aria-label', input.type === 'password' ? 'إظهار كلمة المرور' : 'إخفاء كلمة المرور'); return;
    }
    if (action === 'login') {
      const email = phone.querySelector('input[type=email]');
      const password = phone.querySelector('.inputwrap input');
      if (!email.value || !email.validity.valid || !password.value) { notify('أدخل بريدًا صالحًا وكلمة مرور لتجربة الانتقال. لا تستخدم بيانات حقيقية.'); return; }
      notify('تسجيل دخول توضيحي فقط'); showScreen(5); return;
    }
    if (action === 'otp') {
      const inputs = [...phone.querySelectorAll('.otp-row input')];
      if (inputs.some(i => !i.value)) { const error = phone.querySelector('[data-error]'); error.hidden = false; error.textContent = 'أدخل الرمز المكوّن من ٦ أرقام.'; return; }
      notify('رمز توضيحي؛ لم يتم التحقق من حساب فعلي'); showScreen(4); return;
    }
    if (action === 'resend') {
      button.disabled = true; button.textContent = 'أعد المحاولة بعد ٣٠ ثانية';
      notify('معاينة فقط: لم يتم إرسال بريد إلكتروني');
      setTimeout(() => { button.disabled = false; button.textContent = 'إعادة إرسال الرمز'; }, 30000); return;
    }
    if (action === 'send') { sendMessage(phone); return; }
    if (action === 'book') {
      const day = phone.querySelector('[data-choice=day] [aria-pressed=true]').textContent;
      const time = phone.querySelector('[data-choice=time] [aria-pressed=true]')?.textContent;
      if (!time) { notify('اختار موعدًا متاحًا أولًا'); return; }
      decision('مراجعة طلب المعاينة', `شقة المعادي · ${day} · ${time}. إرسال الطلب ينتظر رد المالك. هذه معاينة توضيحية ولا تُرسل طلبًا فعليًا.`, () => {
        showScreen(11);
        const rows = focusBody.querySelectorAll('.summary-row > b');
        rows[1].textContent = day;
        rows[2].textContent = time;
      }); return;
    }
    if (['accept','accept-detail','reject-detail'].includes(action)) {
      const accepted = action !== 'reject-detail';
      decision(accepted ? 'قبول طلب المعاينة؟' : 'رفض طلب المعاينة؟', 'هذا قرار توضيحي داخل البروبوزال. في التطبيق، يتم تحديث الطلب بعد نجاح استجابة الخادم.', () => updateRequest(button, accepted)); return;
    }
    if (action === 'reset-filters') {
      phone.querySelectorAll('[data-choice]').forEach(c => c.querySelectorAll('button').forEach((b,i) => b.setAttribute('aria-pressed', String(i === 0 && c.dataset.choice !== 'multi'))));
      const range = phone.querySelector('.range'); range.value = 10000; range.dispatchEvent(new Event('input',{bubbles:true}));
      notify('تمت إعادة ضبط الفلاتر التوضيحية'); return;
    }
    const messages = {
      register:'إنشاء الحساب مسار موجود بالتطبيق؛ خارج عينة الـ٢٠ شاشة الحالية.',
      forgot:'يفتح مسار استعادة كلمة المرور الموجود عند التنفيذ.',
      google:'معاينة تصميم فقط؛ تسجيل الدخول بحساب Google غير متصل هنا.',
      upload:'الخطوة التالية في التطبيق: رفع مستندات الهوية ومراجعتها.',
      draft:'تمت معاينة حالة حفظ المسودة. لا يتم حفظ بيانات عقار حقيقية.',
      'next-property':'الخطوة التالية: صور العقار، ثم السعر والمراجعة. المعاينة تعرض خطوة البيانات الأساسية.',
      'visit-details':'تفاصيل المعاينة تعرض الموعد والحالة والإلغاء حسب قواعد الطلب الحالية.',
      report:'الإبلاغ يفتح النموذج الحالي في التطبيق؛ لا يتم إرسال بلاغ من المعاينة.',
      retry:'عينة لحالة إعادة المحاولة؛ لا يوجد اتصال بخادم هنا.'
    };
    notify(messages[action] || 'هذا العنصر يوضح مكان الإجراء في التصميم؛ يُربط بالمسار الحالي وقت التنفيذ.');
  });
  const initialScreen = location.hash.match(/^#S(\d{2})$/);
  if (initialScreen && document.querySelector('.gallery')) showScreen(Number(initialScreen[1]));
})();
