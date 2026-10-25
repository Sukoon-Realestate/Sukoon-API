(() => {
  'use strict';
  const root=document.documentElement, media=matchMedia('(prefers-color-scheme: dark)');
  const data=JSON.parse(document.querySelector('#screen-data').textContent);
  const ids=Object.keys(data), toast=document.querySelector('.toast');
  let mode=new URLSearchParams(location.search).get('theme');
  if(!['light','dark','system'].includes(mode)){try{mode=localStorage.getItem('sukoon-proposal-theme')||'system'}catch{mode='system'}}
  if(!['light','dark','system'].includes(mode))mode='system';
  let timer,focusId,focusPhone,placeholder,confirmAction;
  const focus=document.querySelector('.focus-dialog'),confirm=document.querySelector('.confirm-dialog');
  const renderedState=Object.fromEntries(ids.map(id=>[id,'default']));
  const drafts=new Map();
  function notify(msg){toast.textContent=msg;toast.hidden=false;clearTimeout(timer);timer=setTimeout(()=>toast.hidden=true,4500)}
  function sync(){
    root.dataset.theme=mode==='system'?(media.matches?'dark':'light'):mode;
    root.dataset.mode=mode;
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
    document.querySelectorAll('a[href*="index.html"],a[href*="design-map.html"]').forEach(a=>{const u=new URL(a.href);u.searchParams.set('theme',mode);a.href=u.href});
  }
  media.addEventListener('change',()=>{if(mode==='system')sync()});sync();
  function phone(id){return focusId===id?focusPhone:document.querySelector(`#${id} .phone`)}
  function stash(id){const p=phone(id);drafts.set(id+'|'+renderedState[id],{html:p.querySelector('main').innerHTML,values:[...p.querySelectorAll('input,select,textarea')].map(el=>({value:el.value,checked:el.checked})),scroll:p.querySelector('main').scrollTop,footer:p.querySelector('.phone-footer').innerHTML})}
  function state(id,name){
    const previous=renderedState[id];stash(id);const previousDraft=drafts.get(id+'|'+previous);const p=phone(id);renderedState[id]=name;
    const saved=drafts.get(id+'|'+name);const retained=((['server-error','error','unknown-outcome','saving'].includes(name)&&previous==='default')||(name==='default'&&['server-error','error','unknown-outcome','saving'].includes(previous)))?previousDraft:null;
    const variant=data[id].variants[name];const variantBody=typeof variant==='object'?variant.content:variant;
    p.querySelector('main').innerHTML=saved?.html||(name==='default'?data[id].content:variantBody)||data[id].content;
    p.querySelector('.phone-footer').innerHTML=saved?.footer??(typeof variant==='object'?variant.footer??'':(name==='default'||(name==='server-error'&&['S21','S22','S23','S27','S30','S31','S32','S35','S39'].includes(id))?data[id].footer:''));
    const restoreDraft=retained||saved;if(restoreDraft){p.querySelectorAll('input,select,textarea').forEach((el,i)=>{if(restoreDraft.values[i]){el.value=restoreDraft.values[i].value;el.checked=restoreDraft.values[i].checked}});p.querySelector('main').scrollTop=restoreDraft.scroll}
    document.querySelector(`[data-state="${id}"]`).value=name;
  }
  function restore(){if(focusPhone&&placeholder){placeholder.replaceWith(focusPhone)}focusPhone=null;placeholder=null;focusId=null}
  function show(id){
    if(!data[id]){const n=Number(id.slice(1));const destination=n>=21&&n<=160?'../sprint-'+String(Math.floor((n-21)/20)+1).padStart(2,'0')+'/index.html':'../../index.html';const u=new URL(destination,location.href);u.searchParams.set('theme',mode);u.hash=id;location.href=u.href;return}
    if(focusPhone)restore();
    const p=document.querySelector(`#${id} .phone`);placeholder=document.createElement('div');placeholder.style.height=p.offsetHeight+'px';p.replaceWith(placeholder);focusPhone=p;focusId=id;
    document.querySelector('.focus-body').replaceChildren(p);
    document.querySelector('[data-focus-title]').textContent=document.querySelector(`#${id} .screen-head h2`).textContent;
    document.querySelector('[data-prev]').disabled=ids.indexOf(id)===0;document.querySelector('[data-next]').disabled=ids.indexOf(id)===ids.length-1;
    if(!focus.open)focus.showModal();
  }
  focus.addEventListener('close',restore);
  function ask(title,copy,fn){document.querySelector('[data-confirm-title]').textContent=title;document.querySelector('[data-confirm-copy]').textContent=copy;confirmAction=fn;confirm.showModal()}
  confirm.addEventListener('close',()=>confirmAction=null);
  const represented={"subscriptions":"S88","invoices":"S86","chat-policy":"S92","owner-revenue":"S65","my-housing":"S137",'account-summary':'S42','support-new':'S44','support-tickets':'S46','legal':'S47','business-policies':'S48','guide-settings':'S49','feedback':'S44'};
  const next={
    'my-reviews':'تقييماتي','account-summary':'ملخص حساب المستأجر','subscriptions':'الاشتراكات','invoices':'الفواتير','chat-policy':'مراجعات سياسة المحادثات','legal':'الشروط وسياسة الخصوصية','business-policies':'سياسات الاستخدام','guide-settings':'إرشادات التجربة','contract-document':'مستند العقد','my-housing':'مسكني','support-new':'إنشاء طلب دعم','support-tickets':'طلبات الدعم','feedback':'اقتراح تحسين'
  };
  document.addEventListener('change',ev=>{
    const el=ev.target;
    if(el.matches('[data-state]'))state(el.dataset.state,el.value);
    if(el.id==='group-filter')document.querySelectorAll('.sprint-screen').forEach(s=>s.hidden=el.value!=='all'&&s.dataset.group!==el.value);
    if(el.name==='ack'){const p=el.closest('.phone');p.querySelector('[data-action="delete-account"]').disabled=!el.checked}
  });
  document.addEventListener('input',ev=>{
    if(ev.target.matches('input[name=password],input[name=confirm]'))ev.target.closest('form')?.elements.confirm?.setCustomValidity('');
    if(ev.target.matches('.otp-row input')){ev.target.value=ev.target.value.replace(/[^0-9٠-٩]/g,'').slice(0,1);if(ev.target.value)ev.target.nextElementSibling?.focus()}
    if(ev.target.matches('[data-faq-search]')){const p=ev.target.closest('.phone'),q=ev.target.value.trim();let count=0;p.querySelectorAll('.faq').forEach(d=>{d.hidden=!d.textContent.includes(q);if(!d.hidden)count++});p.querySelector('[data-faq-empty]').hidden=count>0}
  });
  function validPassword(f){const pw=f.elements.password.value,confirmation=f.elements.confirm;confirmation.setCustomValidity('');if(pw!==confirmation.value)confirmation.setCustomValidity('كلمتا المرور غير متطابقتين.');else if(!pw.trim())confirmation.setCustomValidity('لا تستخدم مسافات فقط.');return f.reportValidity()}
  document.addEventListener('submit',ev=>{
    if(!ev.target.matches('[data-form]'))return;ev.preventDefault();const f=ev.target,p=f.closest('.phone'),id=p.dataset.screen;
    if(['register','password'].includes(f.dataset.form)&&!validPassword(f))return;
    switch(f.dataset.form){
      case 'batch-form':{
        if(['unknown-outcome','saving'].includes(renderedState[id])){notify('راجع حالة العملية الأصلية قبل إعادة الإرسال.');break}
        const checks=[...f.querySelectorAll('[data-batch-ack]')];const outputs=checks.filter(c=>['panorama','model'].includes(c.name));
        if(checks.some(c=>!['panorama','model'].includes(c.name)&&!c.checked)||(outputs.length&&!outputs.some(c=>c.checked))){notify('راجع الاختيارات والإقرار المطلوب قبل المتابعة.');break}
        const fields=f.elements;
        if(fields.minBudget&&fields.maxBudget&&Number(fields.minBudget.value)>Number(fields.maxBudget.value)){notify('أقل ميزانية يجب ألا تتجاوز أعلى ميزانية.');break}
        if(fields.start&&fields.end&&fields.end.value<=fields.start.value){notify('تاريخ النهاية يجب أن يكون بعد البداية.');break}
        if(['months','duration','occupants','minutes','keys'].some(k=>fields[k]&&!/^[0-9]+$/.test(fields[k].value))){notify('استخدم أعدادًا صحيحة للقيم المطلوبة.');break}
        const kind=f.dataset.kind;const label=f.querySelector('[type=submit]').dataset.label||'مراجعة الخطوة';
        ask(label,'معاينة محلية فقط. لا يتم إرسال بيانات أو نشر إعلان أو تنفيذ دفع أو توقيع.',()=>{
          let feedback=f.querySelector('.batch-form-feedback');if(!feedback){feedback=document.createElement('div');feedback.className='batch-form-feedback';feedback.setAttribute('role','status');f.append(feedback)}
          feedback.textContent='تمت مراجعة الخطوة محليًا في المعاينة.';
          if(['chat','assistant','case-reply','maintenance-reply'].includes(kind)){
            let thread=p.querySelector('.batch-thread');if(!thread){thread=document.createElement('div');thread.className='batch-thread';f.before(thread)}
            const message=document.createElement('div');message.className='bubble outgoing';message.textContent=fields.message?.value||fields.prompt?.value||fields.reply?.value||'رسالة توضيحية';thread.append(message);
          }
        });break}
      case 'ticket':
        if(renderedState[id]==='unknown-outcome'){notify('راجع حالة الإرسال أولًا.');break}
        ask('إرسال طلب الدعم؟','عرض نتيجة توضيحية فقط. لم يتم إرسال طلب أو ملفات.',()=>show('S45'));break;
      case 'support-reply':{
        if(renderedState[id]==='unknown-outcome'){notify('راجع حالة الرد أولًا.');break}
        const text=f.elements.reply.value.trim();if(!text)break;
        const bubble=document.createElement('div');bubble.className='bubble outgoing';bubble.textContent=text;
        const label=document.createElement('small');label.textContent='رد توضيحي محلي · لم يُرسل';bubble.append(label);
        p.querySelector('.support-messages').append(bubble);f.elements.reply.value='';notify('تمت إضافة رد محلي للمعاينة.');break}
      case 'property-search':{const text=f.elements.query.value.trim();notify(text?'معاينة نتائج البحث عن: '+text:'معاينة البحث بالاختيارات الحالية.');show('S06');break}
      case 'register':notify('معاينة: التسجيل ينتقل لتأكيد البريد ثم تسجيل الدخول.');ask('متابعة لتأكيد البريد؟','سنعرض شاشة الرمز الأصلية. لم يتم إنشاء حساب أو إرسال بريد.',()=>show('S03'));break;
      case 'recovery':{
        const address=f.elements.email.value;const box=document.createElement('div');box.className='panel';const title=document.createElement('h3');title.textContent='راجع بريدك.';const text=document.createElement('p');text.textContent='معاينة فقط: رابط الاستعادة إلى '+address.slice(0,2)+'****@'+address.split('@')[1];box.append(title,text);p.querySelector('main').replaceChildren(box);const b=document.createElement('button');b.className='secondary wide';b.dataset.action='reset-state';b.textContent='تغيير البريد';box.append(b);notify('حالة الإرسال توضيحية. لم نرسل بريدًا.');break}
      case 'profile':notify('معاينة: تُحفظ البيانات بعد نجاح استجابة الخادم.');break;
      case 'password':ask('تغيير كلمة المرور؟','بعد النجاح ينهي التطبيق الجلسة ويطلب تسجيل الدخول. المعاينة لن تغيّر أي بيانات.',()=>show('S02'));break;
      case 'email-old':state(id,'enter-new');break;
      case 'new-email':state(id,'verify-new');break;
      case 'email-new':state(id,'complete');break;
    }
  });
  function mediaReady(p){const count=p.querySelectorAll('.editor-photo').length;p.querySelector('[data-photo-total]').textContent=count+' صور · الحد الأدنى ١٠ والأقصى ٢٥';const invalid=count<10||count>25||p.dataset.videoMissing==='true'||['preparing','duplicate'].includes(renderedState[p.dataset.screen]);p.querySelector('[data-action=media-next]').disabled=invalid;const mains=[...p.querySelectorAll('.main-photo')];if(mains.length&&!mains.some(b=>b.getAttribute('aria-pressed')==='true')){mains[0].setAttribute('aria-pressed','true');mains[0].textContent='رئيسية'}p.querySelector('.inline-feedback').textContent=invalid?'جهّز ١٠–٢٥ صورة وفيديو صالح قبل المتابعة.':''}
  document.addEventListener('click',ev=>{const map=ev.target.closest('[data-pick-map]');if(map&&!ev.target.closest('button')){const p=map.closest('.phone');const pin=map.querySelector('.location-pin');const box=map.getBoundingClientRect();pin.style.left=Math.max(10,Math.min(90,(ev.clientX-box.left)/box.width*100))+'%';pin.style.top=Math.max(10,Math.min(85,(ev.clientY-box.top)/box.height*100))+'%';p.querySelector('[data-action=confirm-location]').disabled=false;const msg=p.querySelector('[data-location-label]');if(msg)msg.textContent='نقطة توضيحية مختارة';return}

    const b=ev.target.closest('button');if(!b)return;
    if(b.dataset.mode){mode=b.dataset.mode;try{localStorage.setItem('sukoon-proposal-theme',mode)}catch{}sync();return}
    if(b.dataset.focus){show(b.dataset.focus);return}
    if(b.hasAttribute('data-close')){focus.close();return}
    if(b.hasAttribute('data-prev')||b.hasAttribute('data-next')){show(ids[ids.indexOf(focusId)+(b.hasAttribute('data-next')?1:-1)]);return}
    if(b.dataset.go){show(b.dataset.go);return}
    if(b.hasAttribute('data-cancel')){confirm.close();return}
    if(b.hasAttribute('data-confirm')){const fn=confirmAction;confirm.close();fn?.();return}
    if(b.dataset.switch){const old=b.getAttribute('aria-checked');b.setAttribute('aria-checked',String(old!=='true'));notify('اختيار محلي للمعاينة. التطبيق يستعيد القيمة السابقة إذا فشل الحفظ.');return}
    const action=b.dataset.action,p=b.closest('.phone'),id=p?.dataset.screen;if(!action)return;
    if(represented[action]){show(represented[action]);return}
    if(next[action]){notify('الخطوة التالية في التطبيق: '+next[action]+'. مجدولة في خطة السبرنتات، ولم تُصمّم هنا.');return}
    if(action==='batch-confirm'){ask(b.dataset.label||b.textContent,'تأكيد محلي للمعاينة فقط. التطبيق يراجع الصلاحية والنسخة ونتيجة الخادم قبل أي تغيير.',()=>notify('تم عرض تأكيد محلي. لم تتغير أي بيانات فعلية.'));return}
    if(action==='batch-recover'){notify('مراجعة المحاولة الأصلية فقط؛ لا يتم تكرار الدفع أو الإرسال.');return}
    if(action==='batch-preview'||action==='batch-next'){notify((b.dataset.label||b.textContent)+' · خطوة توضيحية مرتبطة بصلاحيات وسياق التطبيق.');return}
    if(action==='batch-day'){b.closest('.day-grid').querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));return}
    if(action==='batch-slot'){b.setAttribute('aria-pressed',String(b.getAttribute('aria-pressed')!=='true'));return}
    if(action==='choice'||['support-topic','search-scope','search-type','map-category'].includes(action)){
      b.closest('.chips').querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));
      if(action==='support-topic')p.querySelector('[data-payment-context]').hidden=b.dataset.value!=='payment';
      if(action==='map-category')notify('اختيار محلي لنطاق السكن؛ التطبيق يعيد تحميل النتائج حسب النطاق.');return}
    if(action==='attachment-zoom'){const img=p.querySelector('[data-attachment-image]');const enlarged=img.dataset.zoom==='true';img.dataset.zoom=String(!enlarged);img.style.transform=enlarged?'none':'scale(1.5)';b.textContent=enlarged?'تكبير الصورة':'تصغير الصورة';return}
    if(action==='attachment-video'){notify('معاينة واجهة الفيديو فقط؛ لا يوجد ملف فيديو حقيقي.');return}
    if(action==='ticket-attachment'){const holder=p.querySelector('.sample-attachments');if(holder.children.length>=3){notify('المرفقات هنا عينات توضيحية فقط.');return}const file=document.createElement('div');file.className='sample-file';file.textContent='صورة توضيحية '+(holder.children.length+1);const remove=document.createElement('button');remove.type='button';remove.className='textbtn';remove.textContent='إزالة';remove.dataset.action='remove-ticket-attachment';file.append(remove);holder.append(file);return}
    if(action==='remove-ticket-attachment'){b.closest('.sample-file').remove();return}
    if(action==='open-resolved-ticket'){show('S45');state('S45','resolved');return}
    if(action==='recover-ticket'||action==='recover-reply'){notify('معاينة: مراجعة حالة العملية الأصلية على الخادم، دون إعادة إرسال.');return}
    if(action==='resume-support'){show('S44');notify('التطبيق يستعيد المسودة والملفات المطلوبة قبل المتابعة.');return}
    if(action.startsWith('guide-')){ask('إعادة الشرح؟','عرض توضيحي للإرشادات. التطبيق يراجع صلاحية الوجهة وينتقل للشاشة المناسبة أولًا.',()=>notify('الخطوة ١: اختار الجزء اللي محتاجه، ثم تابع من الإجراء الرئيسي.'));return}
    if(action==='release-version'){state(id,b.dataset.value==='older'?'older-version':'default');return}
    if(action==='retry-startup'){state(id,'default');return}
    if(action==='workspace'){if(['individual','owner'].includes(b.dataset.value)){show(b.dataset.value==='owner'?'S15':'S05')}else notify('مساحة '+(b.dataset.value==='student'?'الطلاب':'الشركات')+' مجدولة لاحقًا؛ اختيارها لا يمنح صلاحيات الحساب.');return}
    if(action==='map-marker'){p.querySelectorAll('[data-marker]').forEach(el=>el.classList.toggle('selected',el===b));const selected=p.querySelector('[data-map-selection]');const template=data[id].content;const doc=new DOMParser().parseFromString(template,'text/html');const photos=[...document.querySelectorAll('#S55 .photo-thumb img')].map(el=>el.src);if(b.dataset.marker==='1'){selected.querySelector('h3').textContent='استوديو مفروش';selected.querySelector('.price').firstChild.textContent='٦٬٠٠٠';if(photos[1])selected.querySelector('img').src=photos[1]}else{selected.innerHTML=doc.querySelector('[data-map-selection]').innerHTML}return}
    if(action==='map-area'){notify('يُفلتر التطبيق النتائج المحمّلة فقط داخل الجزء الظاهر.');return}
    if(action==='map-all'){p.querySelectorAll('[data-marker]').forEach((el,i)=>el.classList.toggle('selected',i===0));notify('معاينة إظهار كل المواقع المحمّلة.');return}
    if(['photo-prev','photo-next','photo-thumb'].includes(action)){
      const thumbs=[...p.querySelectorAll('.photo-thumb')];let index=Number(p.dataset.galleryIndex||0);index=action==='photo-thumb'?Number(b.dataset.index):Math.max(0,Math.min(thumbs.length-1,index+(action==='photo-next'?1:-1)));p.dataset.galleryIndex=String(index);
      p.querySelector('[data-gallery-image]').src=thumbs[index].querySelector('img').src;p.querySelector('[data-gallery-image]').alt=index?'الغرفة الثانية':'غرفة المعيشة';thumbs.forEach((el,i)=>el.setAttribute('aria-pressed',String(i===index)));
      p.querySelector('[data-photo-name]').textContent=index?'الغرفة الثانية':'غرفة المعيشة';p.querySelector('[data-photo-count]').textContent=(index+1)+' / '+thumbs.length;
      p.querySelector('[data-action=photo-prev]').disabled=index===0;p.querySelector('[data-action=photo-next]').disabled=index===thumbs.length-1;return}
    if(action==='save-photo-preview'){notify('في التطبيق: حفظ الصورة بعد مراجعة الإذن. المعاينة لا تحفظ ملفات.');return}
    if(action==='recent-search'){p.querySelector('[name=query]').value=b.querySelector('b').textContent;p.querySelector('[name=query]').focus();return}
    if(action==='current-area'){notify('لم نطلب موقع جهازك. تقدر تكتب المنطقة يدويًا في المعاينة.');return}
    if(action==='visit-chat'){show('S99');notify('الخطوة التالية: بدء محادثة بسياق العقار والمعاينة، مع مراجعة الصلاحيات.');return}
    if(action==='cancel-visit'){ask('إلغاء طلب المعاينة؟','النتيجة التالية توضيحية. التطبيق يغيّر الحالة فقط بعد نجاح الإلغاء.',()=>state(id,'cancelled'));return}
    if(action==='reschedule-visit'){notify('الخطوة التالية: تعديل الموعد بهوية المعاينة ومراجعة الإتاحة على الخادم.');return}
    if(action==='visit-calendar'){notify('التطبيق يشارك حدثًا فقط عندما تكون بيانات المعاينة صالحة للتقويم. لا يُصدر ملف هنا.');return}
    if(action==='owner-tab'){
      b.closest('.tabs').querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));
      const area=p.querySelector('[data-owner-panel]');if(!area){notify('اختر الحالة الأساسية لمراجعة تبديل التبويبات.');return}
      const label={visits:'طلبات المعاينة',demand:'الطلب على السكن',groups:'طلبات المجموعات',offers:'عروض السكن المرسلة'}[b.dataset.value];
      if(b.dataset.value==='visits'){const doc=new DOMParser().parseFromString(data[id].content,'text/html');area.innerHTML=doc.querySelector('[data-owner-panel]').innerHTML}else{area.replaceChildren();const h=document.createElement('h3');h.className='group-title';h.textContent=label;const t=document.createElement('p');t.className='small';t.textContent='قائمة توضيحية. توفر الخدمة وتفاصيل الطلب تُحدد حسب حسابك.';area.append(h,t)}return}
    if(['location-search','locate-demo'].includes(action)){const label=p.querySelector('[data-location-label]');if(label)label.textContent=action==='location-search'?(p.querySelector('[name=address]').value.trim()||'المعادي، القاهرة'):'موقع توضيحي مختار';const confirm=p.querySelector('[data-action=confirm-location]');if(confirm)confirm.disabled=false;notify('موقع توضيحي فقط. لم نصل إلى موقع جهازك أو خدمة خرائط.');return}
    if(action==='satellite-demo'){p.querySelector('.map-stage').classList.toggle('satellite');b.textContent=p.querySelector('.map-stage').classList.contains('satellite')?'عرض الخريطة':'عرض القمر الصناعي';return}
    if(action==='confirm-location'){notify('تمت معاينة تأكيد النقطة المختارة. التطبيق يعيد الإحداثيات إلى النموذج.');return}
    if(action==='remove-property-photo'){b.closest('.editor-photo').remove();mediaReady(p);return}
    if(action==='main-property-photo'){p.querySelectorAll('.main-photo').forEach(el=>{el.setAttribute('aria-pressed',String(el===b));el.textContent=el===b?'رئيسية':'اختيار كرئيسية'});return}
    if(action==='add-property-photo'){const grid=p.querySelector('.photo-editor-grid');if(grid.children.length>=25){notify('الحد الأقصى ٢٥ صورة.');return}const template=new DOMParser().parseFromString(data[id].content,'text/html').querySelector('.editor-photo');const clone=template.cloneNode(true);clone.querySelector('.main-photo').setAttribute('aria-pressed','false');clone.querySelector('.main-photo').textContent='اختيار كرئيسية';grid.append(clone);mediaReady(p);return}
    if(action==='remove-property-video'){p.dataset.videoMissing='true';b.textContent='إضافة عينة فيديو';b.dataset.action='add-property-video';p.querySelector('[data-video-status]').textContent='الفيديو مطلوب قبل المتابعة.';mediaReady(p);return}
    if(action==='add-property-video'){delete p.dataset.videoMissing;b.textContent='إزالة الفيديو';b.dataset.action='remove-property-video';p.querySelector('[data-video-status]').textContent='عينة فيديو جاهزة · ٣٠ ثانية';mediaReady(p);return}
    if(action==='media-next'){show('S61');notify('الخطوة التالية: التسعير. المعاينة لم تنشر العقار أو ترفع الملفات.');return}
    if(['reviews-hub','owner-revenue','visit-review','group-application','housing-offer','accommodation-media'].includes(action)){notify('الوجهة التالية موجودة في خطة السبرنتات؛ لم تُبنَ في هذه الدفعة.');return}
    if(action==='password'){const input=b.previousElementSibling;input.type=input.type==='password'?'text':'password';return}
    if(action==='reset-state'){drafts.delete(id+'|default');drafts.delete(id+'|'+renderedState[id]);renderedState[id]='default';p.querySelector('main').innerHTML=data[id].content;p.querySelector('.phone-footer').innerHTML=data[id].footer;document.querySelector(`[data-state="${id}"]`).value='default';return}
    if(action==='email-start'){state(id,'verify-old');return}
    if(action==='email-restart'){state(id,'default');return}
    if(action==='email-status'){notify('التطبيق يراجع حالة العملية على الخادم قبل إعادة البدء.');return}
    if(action==='resend'){notify('معاينة: إعادة الإرسال تخضع لموعد الخادم وحدود المحاولات.');return}
    if(action==='sample-upload'){b.classList.toggle('selected');b.querySelector('.upload-state').textContent=b.classList.contains('selected')?'✓':'＋';return}
    if(action==='submit-kyc'){
      const idValue=p.querySelector('[name=nationalId]')?.value||'';const selected=p.querySelectorAll('.upload-tile.selected').length;
      if(!/^[23][0-9]{13}$/.test(idValue)||selected!==3){p.querySelector('.inline-feedback').textContent='أدخل رقمًا قوميًّا من ١٤ رقمًا واختر العينات الثلاث. التحقق هنا مبسّط؛ التطبيق يتحقق من التاريخ والمستندات أيضًا.';return}
      ask('إرسال للمراجعة؟','انتقال لحالة انتظار توضيحية. لا تُرفع أي ملفات.',()=>show('S24'));return}
    if(action.startsWith('revoke-')||action==='compromised'){
      ask(b.textContent,'تأكيد محلي فقط. ينفّذ التطبيق الإجراء بعد نجاح الخادم؛ إنهاء الجلسة الحالية أو الكل يعيدك لتسجيل الدخول.',()=>{if(['revoke-current','revoke-all','compromised'].includes(action))show('S02');else {if(action==='revoke-session')b.closest('.panel').remove();else p.querySelectorAll('.session-card').forEach(el=>{if(!el.querySelector('.badge'))el.closest('.panel').remove()});notify('تم عرض نتيجة محلية توضيحية.')}});return}
    if(action==='delete-account'){ask('تأكيد حذف الحساب؟','هذه معاينة فقط. في التطبيق، يجب نجاح الحذف قبل إنهاء الجلسة.',()=>{notify('لم يُحذف حساب. تم عرض نهاية الرحلة التوضيحية.');show('S02')});return}
    if(action==='logout'){ask('تسجيل الخروج؟','عرض رحلة الخروج فقط. لم نتصل بحسابك.',()=>show('S02'));return}
    if(action==='read-all'){p.querySelectorAll('.unread-dot').forEach(el=>el.remove());b.textContent='كل الإشعارات مقروءة · معاينة';return}
    if(action==='notification-related'){show('S11');return}
    if(action==='language-confirm'){notify('تم اختيار '+(p.querySelector('[name=language]:checked').value==='ar'?'العربية':'English')+' للمعاينة. التنفيذ سيطبق اللغة والاتجاه على التطبيق.');return}
    if(action==='avatar'){notify('معاينة اختيار الصورة؛ لا تُفتح صورك أو تُرفع ملفات.');return}
    if(action==='device-settings'){notify('في التطبيق: فتح إعدادات إشعارات الجهاز.');return}
    if(action==='support-email'){notify('التطبيق يستخدم عنوان التواصل الصالح الذي يرسله الخادم.');return}
    notify('عنصر توضيحي مرتبط بسلوك التطبيق الحالي.');
  });
  document.addEventListener('keydown',e=>{if(e.target.matches('[data-pick-map]')&&['Enter',' '].includes(e.key)){e.preventDefault();const p=e.target.closest('.phone');p.querySelector('[data-action=confirm-location]').disabled=false;notify('تم اختيار نقطة توضيحية من لوحة المفاتيح.')}});
  const hash=location.hash.slice(1);if(data[hash]){show(hash)}
})();
