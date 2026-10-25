"""Shared offline renderer. Original S01–S20 remains the visual authority."""
from pathlib import Path
from html import escape as e
import re,json,ast,hashlib
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
WORKSPACE=BASE.parents[3]
APP=WORKSPACE/'sokoun/apps/sokoun_app/lib'
original=(BASE/'original-twenty.html').read_text()
STYLE=re.search(r'<style>(.*?)</style>',original,re.S).group(1)
LOGO=re.search(r'<svg class="atlas-signature".*?</svg>',original,re.S).group(0)
SIGNATURE=re.search(r'<svg class="signature".*?</svg>',original,re.S).group(0)
STATUS=re.search(r'<div class="status\s*">.*?</div>',original,re.S).group(0).replace('class="status "','class="status"')
PHOTOS=list(dict.fromkeys(re.findall(r'<img[^>]+src="(data:image/[^\"]+)"',original)))
ICONS={
 'help':'<circle cx="12" cy="12" r="9"/><path d="M9 8a3 3 0 0 1 6 0c0 2-3 2-3 5m0 3h.01"/>',
 'settings':'<path d="M3 7h18M3 17h18"/><circle cx="8" cy="7" r="3"/><circle cx="16" cy="17" r="3"/>',
 'globe':'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
 'trash':'<path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>',
 'play':'<path d="m8 4 12 8-12 8Z"/>',
}
for file,prefix,suffix in [('build_proposal.py','paths = ','\ndef icon'),('build_atlas.py','source.paths.update(',')\nic =')]:
    literal=(BASE/file).read_text().split(prefix,1)[1].split(suffix,1)[0].strip()
    ICONS.update(ast.literal_eval(literal))
def icon(name):return f'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
def mark(cls='auth-mark'):return LOGO.replace('class="atlas-signature"',f'class="{cls}"')
def button(text,to=None,action=None,kind='primary',extra=''):
    attr=f'data-go="{to}"' if to else f'data-action="{action or "preview"}"'
    return f'<button type="button" class="{kind}" {attr} {extra}>{text}</button>'
def intro(title,sub='',center=False,symbol=None):
    sym=f'<span class="empty-symbol">{icon(symbol)}</span>' if symbol else ''
    return f'<div class="intro auth-intro {"center" if center else ""}">{sym}<h2>{title}</h2>{f"<p>{sub}</p>" if sub else ""}</div>'
def badge(text,kind=''):return f'<span class="badge {kind}">{text}</span>'
def note(text,kind='info',symbol='shield'):return f'<div class="notice {kind}">{icon(symbol)}<p>{text}</p></div>'
def panel(body,cls=''):return f'<div class="panel {cls}">{body}</div>'
def row(text,sub='',to=None,action=None,symbol='arrow'):
    small=f'<small>{sub}</small>' if sub else ''
    return button(f'<span class="row-icon">{icon(symbol)}</span><span class="grow"><b>{text}</b>{small}</span>{icon("arrow")}',to,action,'menu-row')
def section(title,body):return f'<h3 class="group-title">{title}</h3>{panel(body)}'
def field(label,name='',value='',hint='',kind='text',extra=''):
    return f'<label class="field"><span>{label}</span><input type="{kind}" name="{name}" value="{e(value)}" placeholder="{e(hint)}" {extra}></label>'
def textarea(label,name='',value='',hint='',extra=''):
    return f'<label class="field"><span>{label}</span><textarea name="{name}" placeholder="{e(hint)}" {extra}>{e(value)}</textarea></label>'
def summary(rows):return '<div class="summary">'+''.join(f'<div class="summary-row"><span>{a}</span><b>{b}</b></div>' for a,b in rows)+'</div>'
def chips(items,action='choice',selected=0):
    return '<div class="chips">'+''.join(button(t,action=action,kind='chip',extra=f'aria-pressed="{str(i==selected).lower()}" data-value="{v}"') for i,(v,t) in enumerate(items))+'</div>'
def footer(text,action=None,to=None,extra='',kind='primary'):
    return f'<footer class="actions">{button(text,to,action,kind,extra)}</footer>'
def switch(text,sub,key,on=True):
    return f'<div class="switch-row"><span class="grow"><b>{text}</b><small>{sub}</small></span><button type="button" role="switch" aria-label="{text}" aria-checked="{str(on).lower()}" data-switch="{key}"><span></span></button></div>'
def nav(owner=False,active='user'):
    items=[('home','الرئيسية','S15'),('building','عقاراتي','S16'),('chat','الرسائل','S13'),('calendar','الطلبات','S58'),('user','حسابي','S41')] if owner else [('home','الرئيسية','S05'),('heart','المحفوظة','S09'),('chat','الرسائل','S13'),('building','مسكني',None),('user','حسابي','S26')]
    return '<nav class="nav" aria-label="التنقل الرئيسي">'+''.join(button(icon(i)+f'<span>{t}</span>',to,action='my-housing' if to is None else None,kind='active' if i==active else '',extra='aria-current="page"' if i==active else '') for i,t,to in items)+'</nav>'
def compact_property(title='شقة واسعة ومضيئة',price='٨٬٥٠٠',image=0,to='S08'):
    return f'<div class="small-property"><img src="{PHOTOS[image]}" alt="صورة عقار توضيحية"><div class="grow"><h3>{title}</h3><p>المعادي، القاهرة</p><div class="price">{price}<small> ج.م / شهر</small></div></div>{button(icon("arrow"),to=to,kind="iconbtn",extra="aria-label=تفاصيل-العقار")}</div>'
def source(file):
    hits=list(APP.rglob(file))
    if not hits:hits=list((WORKSPACE/'sokoun/packages/core/lib').rglob(file))
    assert len(hits)==1,(file,hits)
    p=hits[0];text=p.read_text()
    return dict(source=str(p.relative_to(WORKSPACE)),sha256=hashlib.sha256(text.encode()).hexdigest(),localeKeys=sorted(set(re.findall(r'LocaleKeys\.(\w+)',text))))
def header(screen):
    if screen.get('chrome')=='launch':return ''
    if screen['id']=='S53':return f'<header class="topbar"><h2>{screen["name"]}</h2></header>'
    if screen.get('hero'):
        h=screen['hero'];extra=button('تعديل الملف',to='S27',kind='brand-edit') if screen['id']=='S41' else ''
        avatar='<span class="avatar">م</span>' if screen['id']=='S41' else ''
        return f'<header class="brandhead">{SIGNATURE}<div class="brandrow">{mark("wordmark")}<span class="workspace">{h[2]}</span>{avatar}{button(icon("settings"),to="S28",kind="iconbtn",extra="aria-label=الإعدادات")}</div><h2>{h[0]}</h2><p>{h[1]}</p>{extra}</header>'
    return f'<header class="topbar">{button(icon("arrow"),to=screen.get("back","S26"),kind="iconbtn",extra="aria-label=رجوع")}<h2>{screen["name"]}</h2></header>'
def render(screens,sprint,out,extra_css='',extra_js=''):
    out.mkdir(exist_ok=True)
    for s in screens:
        if not s.get('variants'):s['variants']={}
    state_labels={'default':'الأساسية','loading':'تحميل','error':'تعذّر التحميل','empty':'فارغة','saving':'حفظ','unknown-outcome':'نتيجة غير مؤكدة','resolved':'مغلقة','payment':'مشكلة دفع','feedback':'اقتراح تحسين','pdf':'ملف PDF','video':'فيديو','session-ended':'انتهت الجلسة','privacy':'الخصوصية','about':'عن سكون','accepted':'سياسات سابقة','unconfirmed':'غير مؤكدة','owner':'مساحة المالك','older-version':'إصدار سابق','recovery-only':'مراجعة العمليات','startup-error':'تعذّر بدء التشغيل','guest':'زائر','selected':'تم الاختيار','map-unavailable':'الخريطة غير متاحة','no-coordinates':'بلا إحداثيات','permission-denied':'الإذن مرفوض','confirmed':'مؤكدة','completed':'مكتملة','cancelled':'ملغاة','stale':'نسخة قديمة','restricted':'خدمات محدودة','groups':'طلبات المجموعات','offers':'عروضي','no-location':'بلا موقع','preparing':'تجهيز الفيديو','duplicate':'صور مكررة','partial-offering':'عرض جزئي'}
    parts=[]
    for s in screens:
        opts='<option value="default">الأساسية</option>'+''.join(f'<option value="{k}">{state_labels.get(k,k)}</option>' for k in s['variants'])
        dark=s.get('hero') or s.get('chrome')=='viewer'
        status=STATUS.replace('class="status"','class="status dark"') if dark else STATUS
        parts.append(f'<article class="screen sprint-screen" id="{s["id"]}" data-group="{s["group"]}"><div class="screen-head"><h2><code>{s["id"]}</code>{s["name"]}</h2><button data-focus="{s["id"]}">تكبير ↗</button></div><label class="state-control">حالة المعاينة <select data-state="{s["id"]}">{opts}</select></label><div class="phone layout-{s.get("layout","utility")} chrome-{s.get("chrome","standard")}" data-screen="{s["id"]}">{status}{header(s)}<main class="phone-scroll">{s["content"]}</main><div class="phone-footer">{s.get("footer","")}</div><div class="home-indicator"></div></div><p class="screen-note">{s["english"]} · <a href="AUDIT.md#{s["id"].lower()}">ملاحظات السلوك</a></p><a class="screen-source" href="../../../../../../{s["source"]}">{s["source"].split("/lib/")[-1]}</a></article>')
    groups=list(dict.fromkeys(s['group'] for s in screens))
    modes='<div class="segmented" aria-label="المظهر">'+''.join(f'<button data-mode="{m}">{t}</button>' for m,t in [('light','فاتح'),('dark','داكن'),('system','حسب الجهاز')])+'</div>'
    filters='<label>المجموعة <select id="group-filter"><option value="all">كل الشاشات · ٢٠</option>'+''.join(f'<option value="{g}">{g}</option>' for g in groups)+'</select></label>'
    body=f'<div class="atlas"><header class="atlas-intro"><div><h1>هوية واحدة. والرحلة بتكمل.</h1><p>سبرنت {sprint} · ٢٠ شاشة جديدة على نسق المقترح الأصلي.</p><p class="sheet-label">{screens[0]["id"]}–{screens[-1]["id"]} · بيانات وتفاعلات محلية توضيحية</p></div>{LOGO}</header><div class="toolbar">{modes}{filters}<a href="../../design-map.html">خريطة التصميم</a><a href="../../index.html">أول ٢٠ شاشة</a><a href="../sprint-01/index.html">سبرنت ١</a><a href="../SPRINT-PLAN.md">خطة السبرنتات</a></div><div class="review-gate"><b>سبرنت {sprint} · جاهز للمراجعة</b><span>السبرنت التالي يبدأ بعد تأكيدك. كل التفاعلات داخل المعاينة فقط.</span></div><div class="gallery">{"".join(parts)}</div><footer class="atlas-footer"><a href="AUDIT.md">تدقيق السلوك</a><a href="screen-manifest.json">بيانات الشاشات</a><span>المقترح مبني على الكود الحالي · لا يوجد اتصال بالخادم.</span></footer></div>'
    body+='<div class="toast" role="status" hidden></div><dialog class="focus-dialog"><div class="focus-controls"><button data-prev>السابق</button><b data-focus-title></b><button data-next>التالي</button><button data-close>إغلاق</button></div><div class="focus-body"></div></dialog><dialog class="confirm-dialog"><h3 data-confirm-title></h3><p data-confirm-copy></p><div class="confirm-actions"><button class="primary" data-confirm>تأكيد المعاينة</button><button class="secondary" data-cancel>إلغاء</button></div></dialog>'
    payload={s['id']:{'content':s['content'],'footer':s.get('footer',''),'variants':s['variants']} for s in screens}
    data=json.dumps(payload,ensure_ascii=False).replace('</','<\\/')
    css=STYLE+'\n'+(HERE/'sprint.css').read_text()+'\n'+extra_css
    js=(HERE/'sprint.js').read_text()+'\n'+extra_js
    (out/'index.html').write_text(f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>سكون · Sprint {sprint} · {screens[0]["id"]}–{screens[-1]["id"]}</title><style>{css}</style></head><body>{body}<script type="application/json" id="screen-data">{data}</script><script>{js}</script></body></html>')
    manifest=[{k:v for k,v in s.items() if k not in ['content','footer','variants','hero']}|{'renderedVariants':list(s['variants'])} for s in screens]
    (out/'screen-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
