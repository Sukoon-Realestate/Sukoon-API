"""Five-sprint design batch: 60 source-audited mockups, no native app writes."""
from sprint_common import *
AUDIT=json.loads((HERE/'batch-08-10-source-audit.json').read_text())
BYFILE={r['file']:r for r in AUDIT}
INVENTORY=json.loads((HERE/'screen-inventory.json').read_text())['screens']
IDS={r['file']:r.get('proposalId') for r in INVENTORY if r.get('proposalId')}
def go(file):return IDS.get(file)
def link(text,file,kind='secondary'):
    target=go(file)
    return button(text,to=target,action=None if target else 'batch-next',kind=kind,extra=f'data-label="{e(text)}"')
def v(body,foot=''):return dict(content=body,footer=foot)
def select(label,name,options):return f'<label class="field"><span>{label}</span><select name="{name}">'+''.join(f'<option value="{i}">{e(t)}</option>' for i,t in enumerate(options))+'</select></label>'
def f(label,name,value='',kind='text',required=True):return field(label,name,value,kind=kind,extra=('required ' if required else '')+('min="1" step="0.01"' if kind=='number' else ''))
def memo(label='ملاحظات',name='note',value='',required=False):return textarea(label,name,value,hint='اكتب التفاصيل هنا…',extra='rows="3" maxlength="4000" '+('required' if required else ''))
def form(body,label='حفظ التغييرات',action='save',unknown=False):
    return f'<form data-form="batch-form" data-kind="{action}">{body}<button type="submit" class="primary wide" data-label="{label}">{label}</button></form>'
def ack(text='راجعت التفاصيل وأوافق على المتابعة.',name='ack'):return f'<label class="ack"><input type="checkbox" name="{name}" data-batch-ack>{text}</label>'
def action(text,kind='secondary',sensitive=False,label=''):
    return button(text,action='batch-confirm' if sensitive else 'batch-preview',kind=kind+' wide',extra=f'data-label="{e(label or text)}"')
def metric(value,label):return f'<div class="stat"><b>{value}</b><small>{label}</small></div>'
def metrics(items):return '<div class="stat-grid">'+''.join(metric(a,b) for a,b in items)+'</div>'
def steps(current,total=3):return f'<div class="step-caption"><span>خطوة {current} من {total}</span><span>بيانات توضيحية</span></div><div class="steps">'+''.join(f'<span class="{"done" if i<current else ""}"></span>' for i in range(total))+'</div>'
def property_block():return compact_property()
def card(title,sub='',status='',target=None,meta=(),action_label='عرض التفاصيل'):
    return panel((badge(status,'warning' if any(x in status for x in ['انتظار','مراجعة','تحقق']) else 'info' if any(x in status for x in ['غير معروف','منته','مغلق']) else '') if status else '')+f'<h3 class="batch-card-title">{title}</h3>'+ (f'<p class="small">{sub}</p>' if sub else '')+(summary(meta) if meta else '')+(link(action_label,target) if target else ''))
def list_cards(items):return ''.join(card(**x) for x in items)
def bars():return '<div class="mini-bars" role="img" aria-label="اتجاهات توضيحية لآخر أسبوع">'+''.join(f'<span style="--bar:{h}%"><i></i><small>{d}</small></span>' for h,d in zip([34,48,42,67,53,82,72],['أحد','إثنين','ثلاثاء','أربعاء','خميس','جمعة','سبت']))+'</div>'
def days(action_name='batch-day'):
    return '<div class="day-grid">'+''.join(button(f'<small>{d}</small><strong>{n}</strong>',action=action_name,kind='day',extra=f'data-index="{i}" aria-pressed="{str(i==0).lower()}"') for i,(d,n) in enumerate([('الإثنين','٢٦'),('الثلاثاء','٢٧'),('الأربعاء','٢٨'),('الخميس','٢٩')]))+'</div>'
def media_art(caption='غرفة المعيشة',capture=False):
    return f'<div class="batch-media"><img src="{PHOTOS[0]}" alt="صورة عقار توضيحية">'+('<div class="capture-reticle"></div>' if capture else '')+f'<span class="media-caption">{caption}</span></div>'
def thread(messages):return '<div class="batch-thread">'+''.join(f'<div class="bubble {"outgoing" if i%2==0 else "incoming"}">{text}<small>نص توضيحي · داخل المعاينة</small></div>' for i,text in enumerate(messages))+'</div>'
def readonly(text):return note(text,'info','lock')
SCREENS=[]
def add(file,name,en,body,behavior,kind='detail',back=None,refs=None,variants=None,hero=None,chrome='standard',states=(),footer_html=''):
    rec=BYFILE[file];sid=rec['proposalId'];deps=rec['dependencies']
    s=dict(id=sid,name=name,english=en,source=rec['source'],sha256=rec['sha256'],localeKeys=rec['localeKeys'],dependencies=deps,group={8:'التغيير والتسوية',9:'مستحقات المالك والتقييمات',10:'المجموعات وسكن الطلاب'}[rec['sprint']],back=go(back) if back else ('S140' if rec['sprint']==8 else 'S26'),content=body,footer=footer_html,variants=variants or {},behavior=behavior,kind=kind,requiredStates=list(dict.fromkeys(['loading','error']+(['empty'] if kind in ['list','hub'] else [])+(['invalid','dirty','saving','unknown-outcome'] if kind in ['form','action','payment','signing'] else ['stale','restricted'])+list(states))),visualReference=refs or (['S17','S20'] if kind in ['form','action'] else ['S18','S19']),sprint=rec['sprint'],chrome=chrome)
    if hero:s['hero']=hero
    SCREENS.append(s)
    return s

