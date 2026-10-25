"""Combine every completed mockup batch into the main offline review page."""
from pathlib import Path
from html import escape
import re,json
ROOT=Path(__file__).resolve().parent
original=ROOT/'original-twenty.html'
assert original.exists(),'Preserve the original 20-screen atlas before building the combined gallery.'
source=original.read_text()
style=re.search(r'<style>(.*?)</style>',source,re.S).group(1)
logo=re.search(r'<svg class="atlas-signature".*?</svg>',source,re.S).group(0)
bridge=(ROOT/'gallery-frame.js').read_text()
collections=[('original','المقترح الأصلي','البداية والرحلة الأساسية',original)]
for directory in sorted((ROOT/'sprints').glob('sprint-*')):
    if not (directory/'index.html').exists():continue
    n=int(directory.name.split('-')[1])
    subtitle={1:'الحساب والهوية والأمان',2:'الدعم والاكتشاف وإدارة المالك',3:'العقار والجولات وأدوات القرار',4:'الخدمات والفوترة والمحادثات',5:'طلبات السكن والتفاوض والمشاركة',6:'الاتفاقات والعقود ومسكني',7:'إدارة الإيجار والتسليم والصيانة'}.get(n,'استكمال رحلة سكون')
    collections.append((directory.name,f'سبرنت {n}',subtitle,directory/'index.html'))
sections=[];catalog=[]
for key,title,subtitle,file in collections:
    doc=file.read_text()
    ids=re.findall(r'<(?:article|section) class="screen[^\"]*" id="(S\d+)"',doc)
    assert ids and len(ids)==len(set(ids)),file
    catalog.append(dict(key=key,title=title,ids=ids))
    # Srcdoc keeps each batch's tested handlers/styles isolated. Relative links
    # retain the batch directory, while all phones are expanded into page flow.
    base='.' if file.parent==ROOT else file.parent.relative_to(ROOT).as_posix()
    doc=re.sub(r'location\.href(?!\s*=)', 'document.baseURI',doc)
    extra='<base href="'+base+'/">'
    extra+='<style>html,body{overflow-y:hidden;scroll-behavior:auto!important}.atlas{padding-top:0!important;padding-bottom:24px!important}.atlas-intro,.toolbar,.atlas-footer,.review-gate{display:none!important}</style>'
    doc=doc.replace('<head>','<head>'+extra,1)
    doc=doc.replace('</body>',f'<script>window.galleryCollection={json.dumps(key)};{bridge}</script></body>')
    sections.append(f'<section class="collection" id="{key}" aria-labelledby="title-{key}"><header class="collection-heading"><div><p class="collection-range">{ids[0]}–{ids[-1]} · {len(ids)} شاشة</p><h2 id="title-{key}">{title} <span>· {subtitle}</span></h2></div><a href="{file.relative_to(ROOT).as_posix()}" target="_blank" rel="noopener">فتح القسم منفصلًا ↗</a></header><iframe class="collection-frame" data-collection="{key}" title="{title} — {subtitle}" srcdoc="{escape(doc,quote=True)}" style="height:4900px" scrolling="no"></iframe></section>')
count=sum(len(c['ids']) for c in catalog)
css='''
.unified-atlas{max-width:1680px;margin:auto;padding-bottom:40px}.unified-heading{padding:42px 40px 0}.unified-heading .atlas-intro{margin-bottom:20px}.unified-heading .sheet-label{font-size:12px}.unified-toolbar{padding-inline:40px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}.unified-toolbar .toolbar{width:100%}.unified-toolbar .maplink{margin-inline-start:auto}.collection-heading{padding:16px 40px 22px;display:flex;justify-content:space-between;align-items:center;gap:20px;border-top:1px solid var(--line);margin-top:28px}.collection-heading h2{font-size:23px;font-weight:600;line-height:1.6}.collection-heading h2 span{font-family:Plex,sans-serif;font-size:16px;font-weight:500;color:var(--muted)}.collection-range{font-size:12px;color:var(--accent);margin-bottom:7px}.collection-heading>a{font-size:12px;white-space:nowrap}.collection-frame{display:block;border:0;width:100%;background:var(--canvas)}.collection{scroll-margin-top:20px}.collection-jumps{display:flex;gap:9px;flex-wrap:wrap;padding:0 40px 12px}.collection-jumps a{padding:8px 13px;border:1px solid var(--line);border-radius:10px;text-decoration:none;background:var(--surface);font-size:12px}.unified-footer{margin:20px 40px 0;padding-top:20px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
@media(max-width:780px){.unified-heading{padding:25px 16px 0}.unified-toolbar{padding-inline:16px}.collection-heading{padding:18px 16px;align-items:start;flex-direction:column;gap:10px}.collection-heading h2{font-size:21px}.collection-heading h2 span{display:block;font-size:14px;margin-top:4px}.collection-jumps{padding-inline:16px}.unified-footer{margin-inline:16px}.unified-toolbar .maplink{margin-inline-start:0}.unified-heading .atlas-intro h1{font-size:27px}.unified-heading .atlas-intro p{font-size:13px}}
'''
mode_buttons=''.join(f'<button data-gallery-mode="{mode}">{text}</button>' for mode,text in [('light','فاتح'),('dark','داكن'),('system','حسب الجهاز')])
options='<option value="all">كل الشاشات · '+str(count)+'</option>'+''.join(f'<option value="{c["key"]}">{c["title"]} · {len(c["ids"])} شاشة</option>' for c in catalog)
jumps=''.join(f'<a href="#{c["key"]}">{c["title"]} · {c["ids"][0]}–{c["ids"][-1]}</a>' for c in catalog)
body=f'<main class="unified-atlas"><div class="unified-heading"><header class="atlas-intro"><div><h1>هوية واحدة. رحلة كاملة.</h1><p>{count} شاشة مكتملة من سكون، بنفس نسق المقترح الأصلي. كل الأقسام معروضة هنا؛ استكشف الشاشات وبدّل المظهر.</p><p class="sheet-label">مقترح UI · بيانات توضيحية · {count} شاشة × وضعين</p></div>{logo}</header></div><div class="unified-toolbar"><div class="toolbar"><div class="segmented" role="group" aria-label="المظهر">{mode_buttons}</div><label>اعرض <select id="collection-filter">{options}</select></label><a class="maplink" href="design-map.html">افتح الـDesign Map</a><span class="theme-label" data-gallery-theme-label></span></div></div><nav class="collection-jumps" aria-label="أقسام المقترح">{jumps}</nav>{"".join(sections)}<footer class="unified-footer">كل الأسماء والصور والبيانات توضيحية. لا تُرسل بيانات أو طلبات. السبرنتات التالية تُضاف بعد مراجعتها.</footer></main>'
init="(()=>{try{let m=new URLSearchParams(location.search).get('theme')||localStorage.getItem('sukoon-proposal-theme')||'system';document.documentElement.dataset.theme=m==='dark'||(m==='system'&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light'}catch{}})()"
js=(ROOT/'gallery.js').read_text().replace('__COLLECTIONS__',json.dumps(catalog,ensure_ascii=False))
(ROOT/'index.html').write_text(f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>سكون · كل الشاشات · {count}</title><script>{init}</script><style>{style}\n{css}</style></head><body>{body}<script>{js}</script></body></html>')
print(f'Built main gallery: {count} screens in {len(catalog)} titled sections.')
