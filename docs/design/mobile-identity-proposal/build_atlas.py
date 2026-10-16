"""Build the offline, 20-screen identity atlas and implementation design map."""
from pathlib import Path
import base64
import json
from html import escape
import build_proposal as source

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
source.paths.update({
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
    'moon': '<path d="M21 13a9 9 0 0 1-10-10 9 9 0 1 0 10 10Z"/>',
    'device': '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/>',
    'eye': '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
    'lock': '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    'send': '<path d="m22 2-7 20-4-9-9-4Zm0 0L11 13"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'file': '<path d="M14 2H5v20h14V7Zm0 0v5h5M8 12h8m-8 4h8"/>',
    'camera': '<path d="m8 5 2-3h4l2 3h5v15H3V5Z"/><circle cx="12" cy="12" r="4"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
    'close': '<path d="m6 6 12 12M6 18 18 6"/>',
    'star': '<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>',
    'wifi': '<path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-10 4a5 5 0 0 1 6 0m-3 4h.01"/>',
    'battery': '<rect x="2" y="6" width="17" height="12" rx="2"/><path d="M22 10v4M5 9h10v6H5Z"/>',
    'signal': '<path d="M4 18v2m5-7v7m5-12v12m5-17v17"/>',
})
ic = source.icon
photo, studio = source.photo, source.studio

def wordmark(cls='wordmark'):
    return f'<svg class="{cls}" viewBox="0 0 1455 811" role="img" aria-label="سكون"><path d="{source.sig}" fill="currentColor"/></svg>'

def signature():
    return source.signature()

def btn(text, cls='primary', go=None, action=None, extra=''):
    attr = f'data-go="{go}"' if go else (f'data-action="{action}"' if action else 'data-preview="true"')
    return f'<button type="button" class="{cls}" {attr} {extra}>{text}</button>'

def iconbtn(name, label, go=None, action=None):
    return btn(ic(name),'iconbtn',go,action,f'aria-label="{label}"')

def badge(text='ملكية موثّقة', kind='', icon=None):
    return f'<span class="badge {kind}">{ic(icon) if icon else ""}{text}</span>'

def status(hero=False):
    return f'<div class="status {"dark" if hero else ""}"><b>9:41</b><span class="island"></span><span class="systemicons">{ic("signal")}{ic("wifi")}{ic("battery")}</span></div>'

def bar(title, back=5, action=None):
    return f'<header class="topbar">{iconbtn("arrow","رجوع",back)}<h2>{title}</h2>{action or ""}</header>'

def brand(title, sub='', owner=False, search=False):
    brandrow = '<span class="workspace">حساب المالك</span>' if owner else wordmark()+f'<span class="place">{ic("pin")} القاهرة</span>'
    return f'<header class="brandhead">{signature()}<div class="brandrow">{brandrow}<span class="avatar">{"م" if owner else "أ"}</span></div><h2>{title}</h2>{f"<p>{sub}</p>" if sub else ""}{searchbox() if search else ""}</header>'

def searchbox(value='ابحث بالمنطقة أو اسم العقار', go=6):
    return btn(ic('search')+f'<span>{value}</span>'+ic('filter'),'searchbox',go)

def nav(active='home', owner=False):
    items = [('home','الرئيسية',15),('building','عقاراتي',16),('calendar','الطلبات',18),('chat','الرسائل',13),('user','حسابي',20)] if owner else [('home','الرئيسية',5),('heart','المحفوظة',9),('calendar','المعاينات',12),('chat','الرسائل',13),('user','حسابي',20)]
    return '<nav class="nav" aria-label="التنقل الرئيسي">'+''.join(btn(ic(n)+f'<span>{t}</span>', 'active' if n==active else '', go, extra='aria-current="page"' if n==active else '') for n,t,go in items)+'</nav>'

def actions(text, go=None, side=None, action=None):
    return f'<footer class="actions">{btn(text,go=go,action=action)}{side or ""}</footer>'

def scroll(content, cls=''):
    return f'<main class="phone-scroll {cls}">{content}</main>'

def phone(n, content, hero=False):
    return f'<div class="phone" data-screen="{n}">{status(hero)}{content}<div class="home-indicator"></div></div>'

def chips(items, selected=0, group='single'):
    return f'<div class="chips" data-choice="{group}">'+''.join(f'<button class="chip" aria-pressed="{str(i==selected).lower()}">{v}</button>' for i,v in enumerate(items))+'</div>'

def tabs(items, selected=0, scope='local'):
    return f'<div class="tabs" data-tabs="{scope}">'+''.join(f'<button aria-pressed="{str(i==selected).lower()}" data-tab="{i}">{t}</button>' for i,t in enumerate(items))+'</div>'

def title(text, link=None, go=None):
    return f'<div class="sectiontitle"><h3>{text}</h3>{btn(link,"",go) if link else ""}</div>'

def save(saved=False):
    return btn(ic('heart'),'savebtn',action='save',extra=f'aria-label="حفظ العقار" aria-pressed="{str(saved).lower()}"')

def property_card(second=False, saved=False, management=False):
    img,t,loc,p = (studio,'استوديو مفروش','مدينة نصر، القاهرة','٦٬٠٠٠') if second else (photo,'شقة واسعة ومضيئة','المعادي، القاهرة','٨٬٥٠٠')
    stamp = badge('قيد المراجعة','warning') if management and second else badge('منشور' if management else 'ملكية موثّقة', icon=None if management else 'shield')
    return f'<article class="property"><div class="property-media"><img src="{img}" alt="صورة عقار توضيحية">{stamp}{"" if management else save(saved)}</div><div class="property-copy"><div class="row spread"><button class="property-link" data-go="8">{t}</button></div><p class="location">{ic("pin")}{loc}</p><div class="price">{p}<small> ج.م / شهر</small></div><div class="facts"><span>{ic("bed")}{"غرفة" if second else "غرفتان"}</span><span>{ic("bath")}حمّام</span><span>{ic("area")}{"٦٠" if second else "١٢٠"} م²</span></div></div>{f"<div class=property-management>{btn('تعديل العقار','secondary',17)}{btn('عرض التفاصيل','secondary',8)}</div>" if management else ""}</article>'

def small_property(second=False):
    return f'<div class="small-property"><img src="{studio if second else photo}" alt="صورة العقار"><div class="grow"><h3>{"استوديو مفروش" if second else "شقة واسعة ومضيئة"}</h3><p>{"مدينة نصر" if second else "المعادي"}، القاهرة</p><div class="price">{"٦٬٠٠٠" if second else "٨٬٥٠٠"}<small> ج.م / شهر</small></div></div></div>'

def field(label, placeholder='', value='', kind='text', extra=''):
    return f'<label class="field"><span>{label}</span><input type="{kind}" placeholder="{placeholder}" value="{value}" {extra}></label>'

def notice(text, kind='', icon='shield'):
    return f'<div class="notice {kind}">{ic(icon)}<p>{text}</p></div>'

def summary(rows):
    return '<div class="summary">'+''.join(f'<div class="summary-row"><span>{a}</span><b>{b}</b></div>' for a,b in rows)+'</div>'

def request(name='أحمد محمود', initial='أ', second=False, confirmed=False):
    state='confirmed' if confirmed else 'pending'
    return f'<article class="request" data-request-state="{state}"><div class="row"><span class="avatar">{initial}</span><div class="requestname"><b>{name}</b><span>{ic("shield")} هوية موثّقة</span></div>{badge("مؤكدة" if confirmed else "بانتظارك", "" if confirmed else "warning")}</div><div class="request-meta">{ic("building")}{"استوديو مدينة نصر" if second else "شقة المعادي"}</div><div class="request-meta">{ic("calendar")}{"الجمعة ٢٣ أكتوبر · ٤:٣٠ م" if second else "الخميس ٢٢ أكتوبر · ٦:٠٠ م"}</div>{f"<div class=request-actions>{btn('قبول المعاينة', action='accept')}{btn('التفاصيل','secondary',19)}</div>" if not confirmed else '<div class="request-status">تم تأكيد موعد المعاينة</div>'}</article>'

def visit(pending=False, second=False):
    return f'<article class="visit">{small_property(second)}<div class="row spread"><span class="small">{ic("calendar")} الخميس ٢٢ أكتوبر</span>{badge("بانتظار المالك" if pending else "مؤكدة","warning" if pending else "")}</div><p class="small" style="margin-top:8px">{ic("clock")} ٦:٠٠ مساءً</p><div class="visit-actions">{btn("تواصل مع المالك","secondary",14)}{btn("تفاصيل المعاينة","textbtn",action="visit-details")}</div></article>'

screens=[]
def add(n,name,group,file,content,note,components,states,hero=False):
    paths=list((ROOT/'mobile/apps/sokoun_app/lib/features').rglob(file))
    assert len(paths)==1,(file,paths)
    screens.append(dict(id=f'S{n:02}',number=n,name=name,group=group,source=str(paths[0].relative_to(ROOT)).replace('\\','/'),note=note,components=components,states=states,html=phone(n,content,hero)))

# Account access is email/password in the current app. OTP verifies email.
add(1,'الترحيب','account','welcome_screen.dart',
    f'<div class="welcome-art">{signature()}{wordmark("welcome-logo")}<img src="{photo}" alt="منزل بإضاءة طبيعية"></div>'+scroll(f'<div class="welcome-copy"><h2>سكنك القادم،<br>من المالك مباشرة.</h2><p>مكان واحد يجمعك بصاحب العقار، من أول بحث لحد المعاينة.</p><div class="welcome-benefits"><span>{ic("shield")} حسابات موثّقة</span><span>{ic("chat")} تواصل مباشر</span></div>{btn("إنشاء حساب","primary wide",action="register")}{btn("عندك حساب؟ سجّل الدخول","textbtn wide",2)}</div>'),
    'القوس والصورة وتوقيع سكون يربطوا أول لحظة بالـlanding.', ['BrandArch','Wordmark','PrimaryButton'],['default'],True)
login = wordmark('auth-mark')+'<div class="auth-intro"><h2>أهلًا برجوعك.</h2><p>سجّل دخولك وكمّل رحلتك مع سكون.</p></div>'+field('البريد الإلكتروني','name@example.com',kind='email',extra='autocomplete="off" dir="ltr"')+f'<label class="field"><span>كلمة المرور</span><div class="inputwrap"><input type="password" placeholder="أدخل كلمة المرور" autocomplete="off">{iconbtn("eye","إظهار كلمة المرور",action="password")}</div></label>'+btn('نسيت كلمة المرور؟','textbtn',action='forgot')+btn('تسجيل الدخول','primary wide',action='login')+'<div class="divider">أو</div>'+btn('المتابعة باستخدام Google','secondary wide',action='google')+btn('تصفّح كزائر','textbtn wide',5)+'<p class="auth-bottom">جديد في سكون؟ '+btn('إنشاء حساب','',action='register')+'</p>'
add(2,'تسجيل الدخول','account','login_screen.dart',bar('تسجيل الدخول',1)+scroll(login),'نفس حقول البريد وكلمة المرور الموجودة، بوضوح أكبر.', ['TextField','PasswordField','AuthActions'],['empty','invalid email','loading','server error'])
otp = '<div class="empty-symbol">'+ic('mail')+'</div><div class="auth-intro center"><h2>راجع بريدك.</h2><p>أدخل الرمز المكوّن من ٦ أرقام المرسل إلى<br><b dir="ltr">ah****@gmail.com</b></p></div><div class="otp-row">'+''.join(f'<input aria-label="الرقم {i+1}" inputmode="numeric" maxlength="1" autocomplete="off" pattern="[0-9]">' for i in range(6))+'</div><div class="error-message" data-error hidden></div><p class="small center muted">لم يصلك الرمز؟</p>'+btn('إعادة إرسال الرمز','textbtn wide',action='resend')+'<div class="spacer"></div>'+btn('تأكيد البريد الإلكتروني','primary wide',action='otp')+notice('رمز التحقق خاص بحسابك. لا تشاركه مع أي شخص.','info','lock')
add(3,'تأكيد البريد','account','otp_screen.dart',bar('رمز التحقق',2)+scroll(otp),'٦ خانات LTR داخل شاشة RTL؛ الرمز يخص البريد كما في الكود.', ['OtpField','ResendTimer','InlineError'],['incomplete','expired','invalid','resend cooldown','verifying'])
kyc='<div class="step-caption"><span>توثيق الحساب</span><span>١ من ٢</span></div><div class="steps"><span class="done"></span><span></span></div><h2>خلّي الثقة<br>أول خطوة.</h2><p style="margin-top:12px">جهّز المستندات التالية عشان نراجع هويتك.</p>'
for i,t,d in [('file','بطاقة هوية سارية','صورة واضحة للوجه الأمامي والخلفي.'),('camera','صورة شخصية','إضاءة واضحة وملامح الوجه ظاهرة.')]:
    kyc+=f'<div class="requirement">{ic(i)}<div><h3>{t}</h3><p>{d}</p></div></div>'
kyc+=notice('مستندات التوثيق مخصّصة لمراجعة الهوية، ولا تظهر في ملفك العام.','info','lock')
add(4,'توثيق الهوية','account','kyc_intro_screen.dart',bar('توثيق الهوية',2)+scroll(kyc)+actions('رفع المستندات',action='upload'),'متطلبات واضحة، مع رسالة خصوصية بجوار خطوة الرفع.', ['ProgressSteps','RequirementRow','PrivacyNotice'],['not started','upload next','pending review','rejected','approved'])
add(5,'الرئيسية للمستأجر','tenant','tenant_home_screen.dart',brand('مكانك الجاي،<br>على راحتك.',search=True)+scroll(chips(['الكل','شقة','استوديو','فيلا'],group='home-type')+title('عقارات مقترحة لك','عرض الكل',6)+property_card()+property_card(True))+nav(),'الهوية في الهيدر، والمعلومة الأساسية في كارت العقار.', ['BrandHeader','SearchField','PropertyCard','BottomNav'],['loading','cached results','empty','error'],True)
results=searchbox('المعادي، القاهرة')+'<div class="spacer"></div><div class="row spread">'+badge('المعادي')+btn(ic('filter')+' فلترة','secondary',7)+'</div>'+title('نتائج البحث','الخريطة',None)+'<p class="small muted" style="margin-bottom:14px">عقاران يطابقان البحث التوضيحي</p>'+property_card()+property_card(True)
add(6,'نتائج البحث','tenant','tenant_search_results_screen.dart',bar('نتائج البحث',5)+scroll(results)+nav(),'فلاتر ظاهرة، وسعر وموقع سهلين للمقارنة.', ['SearchField','FilterChip','PropertyCard'],['loading','no matches','error','refresh notice'])
filters='<section class="filter-section"><h3>نوع العقار</h3>'+chips(['شقة','استوديو','غرفة','فيلا'],group='multi')+'</section><section class="filter-section"><h3>السعر الشهري</h3><div class="row spread"><span class="small muted">حتى</span><b data-price-output>١٠٬٠٠٠ ج.م</b></div><input class="range" type="range" min="1000" max="20000" value="10000" step="500" aria-label="الحد الأقصى للسعر"><div class="range-labels"><span>١٬٠٠٠ ج.م</span><span>٢٠٬٠٠٠ ج.م</span></div></section><section class="filter-section"><h3>عدد الغرف</h3>'+chips(['أي عدد','١','٢','٣','٤+'])+'</section><section class="filter-section"><h3>المرافق</h3>'+chips(['مفروش','مكيّف','مصعد','جراج'],group='multi')+'</section>'+field('المنطقة','اختر المنطقة','المعادي، القاهرة')
add(7,'فلترة العقارات','tenant','tenant_filter_screen.dart',bar('فلترة النتائج',6,btn('إعادة ضبط','textbtn',action='reset-filters'))+scroll(filters)+actions('عرض النتائج',6),'فلترة قابلة للمس؛ الاختيارات واضحة في الوضعين.', ['FilterChip','PriceRange','StickyAction'],['selected','unselected','no results','reset'])
detailhero=f'<div class="detail-photo"><img src="{photo}" alt="غرفة معيشة مضيئة">{btn(ic("arrow"),"iconbtn back-photo",6,extra="aria-label=رجوع")}{save()}<span class="photo-count">١ / ٨ صور</span></div>'
details=badge('تم التحقق من الملكية',icon='shield')+'<h2>شقة واسعة ومضيئة<br>في قلب المعادي</h2><p class="location">'+ic('pin')+' المعادي، القاهرة</p><div class="detail-price"><strong>٨٬٥٠٠</strong><small>ج.م / شهر</small>'+badge('مفروش')+'</div><div class="metrics"><span>'+ic('bed')+'غرفتان</span><span>'+ic('bath')+'حمّام</span><span>'+ic('area')+'١٢٠ م²</span></div><div class="owner-row"><span class="avatar">م</span><div><b>محمد أحمد</b><small>مالك العقار</small></div>'+badge('موثّق',icon='shield')+'</div><h3>عن العقار</h3><p class="small" style="margin-top:7px">شقة بإضاءة طبيعية وبلكونة واسعة، في شارع هادئ وقريبة من الخدمات.</p>'+summary([('مدة الإيجار','سنة'),('الدور','الثالث'),('المرافق','مصعد · تكييف · بلكونة')])
add(8,'تفاصيل العقار','tenant','property_details_screen.dart',detailhero+scroll(details,'detail-scroll')+actions(ic('calendar')+' احجز معاينة',10,btn(ic('chat'),'secondary',14,extra='aria-label="تواصل مع المالك"')),'الصورة والثقة والسعر أولًا؛ حجز المعاينة ثابت أسفل الشاشة.', ['PropertyGallery','VerificationBadge','FactsRow','ActionFooter'],['loading','unverified','saved','own property','chat unavailable'])
add(9,'العقارات المحفوظة','tenant','favorites_screen.dart',bar('المحفوظة',5)+scroll('<h2>أماكن تستاهل<br>ترجع لها.</h2><p class="small" style="margin:10px 0 20px">عقاران في قائمتك</p>'+property_card(saved=True)+property_card(True,True))+nav('heart'),'نفس كارت العقار؛ الحفظ حالة واضحة وليه بديل فارغ.', ['PropertyCard','SaveToggle','EmptyState'],['populated','empty','remove','error'])
days='<div class="day-grid" data-choice="day">'+''.join(f'<button class="day" aria-pressed="{str(i==0).lower()}">{d}<strong>{n}</strong>أكتوبر</button>' for i,(d,n) in enumerate([('الخميس','٢٢'),('الجمعة','٢٣'),('السبت','٢٤'),('الأحد','٢٥')]))+'</div>'
times='<div class="time-grid" data-choice="time">'+''.join(f'<button class="chip" aria-pressed="{str(i==1).lower()}" {"disabled" if i==0 else ""}>{v}</button>' for i,v in enumerate(['٤:٠٠ م','٦:٠٠ م','٧:٣٠ م']))+'</div>'
booking=small_property()+title('اختر يوم المعاينة')+days+title('المواعيد المتاحة')+times+'<label class="field"><span>ملاحظة للمالك <small class="muted">(اختياري)</small></span><textarea placeholder="أي تفاصيل تحب توضحها قبل الزيارة"></textarea></label>'+notice('إرسال الطلب لا يؤكد المعاينة؛ هتوصلك حالة الطلب بعد رد المالك.','warning','clock')
add(10,'حجز معاينة','tenant','book_visit_screen.dart',bar('حجز معاينة',8)+scroll(booking)+actions('مراجعة طلب المعاينة',action='book'),'اختيار اليوم والوقت ثم مراجعة الطلب، مع توضيح انتظار المالك.', ['DayPicker','TimeSlot','NoteField','ReviewSheet'],['available','unavailable','loading slots','slot changed','submitting'])
sent='<div class="empty-symbol">'+ic('check')+'</div><div class="center"><h2>تم إرسال<br>طلب المعاينة.</h2><p style="margin-top:12px">بانتظار رد المالك لتأكيد الموعد.<br>تابع حالة طلبك من المعاينات.</p></div>'+summary([('العقار','شقة المعادي'),('اليوم','الخميس ٢٢ أكتوبر'),('الوقت','٦:٠٠ مساءً'),('الحالة',badge('بانتظار المالك','warning'))])+btn('متابعة طلباتي','primary wide',12)+btn('العودة للرئيسية','textbtn wide',5)
add(11,'تم إرسال الطلب','tenant','visit_confirmed_screen.dart',scroll(sent),'نجاح إرسال الطلب مع إبراز أن الموعد لسه بانتظار المالك.', ['SuccessMessage','VisitSummary','StatusBadge'],['request sent / owner pending'])
add(12,'معايناتي','tenant','tenant_visits_screen.dart',bar('المعاينات',5)+scroll(tabs(['القادمة','السابقة'],scope='visits')+'<div data-visit-list>'+visit()+visit(True,True)+'</div>')+nav('calendar'),'موعد وحالة لكل معاينة؛ الحالة مكتوبة بجوار اللون.', ['VisitCard','StatusTabs','EmptyState'],['pending','confirmed','completed','cancelled','empty'])
chats=searchbox('ابحث في المحادثات',13)
for n,initial,msg,time,unread in [('محمد أحمد','م','أكيد، المعاينة يوم الخميس الساعة ٦.','١٠:٣٢',2),('سارة علي','س','الاستوديو متاح للمعاينة الأسبوع ده.','أمس',0),('كريم حسن','ك','شكرًا لتواصلك، هراجع التفاصيل.','الثلاثاء',0)]:
    chats+=f'<button class="list-row" data-go="14"><span class="avatar">{initial}</span><div class="grow"><h3>{n}</h3><p>{msg}</p></div><div class="meta">{time}{f"<span class=unread>{unread}</span>" if unread else ""}</div></button>'
add(13,'المحادثات','shared','chats_screen.dart',bar('الرسائل',5)+scroll(chats)+nav('chat'),'قائمة هادية؛ عدد غير المقروء ظاهر من غير ازدحام.', ['ConversationRow','UnreadBadge','SearchField'],['loading','empty','unread','restricted','offline'])
thread='<div class="chat-date">الخميس ٢٢ أكتوبر</div><div class="bubble outgoing">مساء الخير، الشقة لسه متاحة؟<small>١٠:٢٥ ص · تم الإرسال</small></div><div class="bubble">أهلًا أحمد، أيوه متاحة. تحب تعاينها إمتى؟<small>١٠:٢٧ ص</small></div><div class="bubble outgoing">يناسبني الخميس الساعة ٦ مساءً.<small>١٠:٣٠ ص · تم الإرسال</small></div><div class="bubble">أكيد، ابعت طلب المعاينة من صفحة العقار عشان نثبت الموعد.<small>١٠:٣٢ ص</small></div>'+notice('خليك على تواصل داخل سكون لمتابعة تفاصيل المعاينة.','info','chat')
add(14,'محادثة المالك','shared','chat_screen.dart',bar('محمد أحمد',13,iconbtn('shield','الإبلاغ عن المحادثة',action='report'))+f'<div class="chat-context">{small_property()}</div>'+scroll(thread,'thread-scroll')+'<form class="composer"><input aria-label="رسالتك" placeholder="اكتب رسالتك هنا…" maxlength="1000">'+btn(ic('send'),action='send',extra='aria-label="إرسال الرسالة"')+'</form>','العقار يفضل في السياق، والرسائل متباينة في الوضعين.', ['ChatContext','MessageBubble','Composer'],['sending','sent','failed','restricted','disconnected'])
ownerhome=title('طلبات تحتاج ردك','عرض الكل',18)+request()+title('نظرة على عقاراتك')+'<div class="stats">'+''.join(f'<div class="stat"><strong>{v}</strong><span>{label}</span></div>' for v,label in [('٣','عقارات نشطة'),('٥','معاينات هذا الأسبوع'),('٢','طلبات بانتظارك'),('٤٫٨','متوسط التقييم')])+'</div>'+btn(ic('plus')+'<span class="grow"><b>أضف عقارًا جديدًا</b><small>ابدأ بالبيانات الأساسية</small></span>'+ic('arrow'),'quick-action',17)
add(15,'الرئيسية للمالك','owner','owner_home_screen.dart',brand('أهلًا، محمد.','تابع عقاراتك ومعايناتك من مكان واحد.',True)+scroll(ownerhome)+nav('home',True),'الطلبات قبل الإحصائيات، مع نفس اللون الأساسي للمستأجر.', ['BrandHeader','RequestCard','OwnerStats','QuickAction'],['loading','no properties','no requests','partial error'],True)
add(16,'عقاراتي','owner','owner_properties_screen.dart',bar('عقاراتي',15,iconbtn('plus','إضافة عقار',17))+scroll(tabs(['الكل','المنشورة','قيد المراجعة'],scope='properties')+property_card(management=True)+property_card(True,management=True))+nav('building',True),'حالة النشر منفصلة عن التوثيق، والتعديل ظاهر لكل عقار.', ['ManagedPropertyCard','StatusTabs','PropertyActions'],['published','pending review','rejected','draft','empty'])
addform='<div class="step-caption"><span>البيانات الأساسية</span><span>١ من ٣</span></div><div class="steps"><span class="done"></span><span></span><span></span></div><h2>عرّفنا على عقارك.</h2><p class="small" style="margin:10px 0 20px">ابدأ بالنوع والموقع والتفاصيل الأساسية.</p>'+field('عنوان الإعلان','عنوان واضح للعقار','شقة واسعة ومضيئة في المعادي')+title('نوع العقار')+chips(['شقة','استوديو','فيلا'])+'<div class="spacer"></div>'+field('المحافظة','اختر المحافظة','القاهرة')+field('المنطقة','اختر المنطقة','المعادي')+'<div class="field-pair">'+field('الغرف',value='٢')+field('الحمّامات',value='١')+'</div>'+field('المساحة بالمتر المربع',value='١٢٠')+'<div class="draftnote">'+ic('file')+' مسودة توضيحية؛ لم يتم نشر العقار</div>'
add(17,'إضافة عقار','owner','owner_property_flow_screen.dart',bar('إضافة عقار',16,btn('حفظ','textbtn',action='draft'))+scroll(addform)+actions('التالي: الصور',action='next-property'),'الخطوة الأولى من الإضافة؛ تقدم واضح وحفظ المسودة.', ['StepProgress','TextField','TypeChip','DraftFeedback'],['draft','validation errors','saving','upload next','unsaved changes'])
add(18,'طلبات المعاينة','owner','owner_visit_requests_screen.dart',brand('طلبات المعاينة','كل طلب، خطوة أقرب لمستأجرك.',True)+scroll(tabs(['الكل','بانتظارك','مؤكدة'],scope='requests')+request()+request('نور خالد','ن',True)+request('كريم حسن','ك',confirmed=True))+nav('calendar',True),'الطلبات قابلة للفلترة؛ التأكيد خطوة مستقلة قبل تغيير الحالة.', ['RequestCard','StatusTabs','ConfirmationSheet'],['pending','confirmed','rejected','no matches','updating'],True)
requestdetails='<div class="profilehero"><span class="avatar">أ</span><h3>أحمد محمود</h3>'+badge('هوية موثّقة',icon='shield')+'</div>'+small_property()+summary([('الموعد المطلوب','الخميس ٢٢ أكتوبر'),('الوقت','٦:٠٠ مساءً'),('حالة الطلب',badge('بانتظار قرارك','warning'))])+'<h3>ملاحظة المستأجر</h3><p class="small" style="margin-top:8px">حابب أشوف الشقة وأعرف تفاصيل مدة الإيجار.</p>'+notice('عند القبول، يتم تحديث حالة الطلب وإبلاغ المستأجر.','info','calendar')+btn('مراسلة المستأجر','secondary wide',14)
add(19,'تفاصيل طلب المعاينة','owner','owner_request_details_screen.dart',bar('تفاصيل الطلب',18)+scroll(requestdetails)+actions('قبول الطلب',side=btn('رفض','destructive',action='reject-detail'),action='accept-detail'),'تفاصيل الشخص والعقار والوقت قبل قبول أو رفض الطلب.', ['ApplicantIdentity','VisitSummary','DecisionFooter'],['pending','confirmed','rejected','verification warning','updating'])
appearance='<h2>سكون، على مزاجك.</h2><p style="margin:10px 0 22px">اختار المظهر اللي يريح عينيك، أو خلّيه يتغيّر مع جهازك.</p>'
for mode,label,desc in [('system','حسب إعدادات الجهاز','يتبع الوضع الفاتح أو الداكن في جهازك'),('light','فاتح','خلفيات ورقية وأخضر عميق'),('dark','داكن','أخضر ليلي وتباين مريح للقراءة')]:
    appearance+=f'<button class="theme-option" data-mode="{mode}" aria-pressed="false"><span class="mini-theme {mode}"></span><span><b>{label}</b><small>{desc}</small></span><span class="radio"></span></button>'
appearance+=notice('اختيارك بيتحفظ على الجهاز. تقدر تغيّره في أي وقت.','','device')
add(20,'المظهر','shared','appearance_screen.dart',bar('المظهر',5)+scroll(appearance),'تبديل فعلي لكل الشاشات؛ فاتح وداكن وحسب الجهاز.', ['ThemeOption','ThemePreview','SystemPreference'],['system','light','dark','persisted preference'])

TOKENS = {
 'canvas':('#F6F2E9','#0A120D','خلفية الشاشة'), 'surface':('#FCFBF7','#0E1912','البطاقات والحقول'),
 'raised':('#ECE5D5','#16241B','سطح مرتفع / هيكل التحميل'), 'text':('#0C2A18','#ECF2EA','النص الأساسي'),
 'muted':('#4B5650','#A1B0A6','النص الثانوي'), 'line':('#E3DCCB','#294632','فصل الأسطح'),
 'accent':('#0A5C18','#7FE08D','الروابط والاختيار'), 'chip':('#E1F0E2','#173A24','الاختيارات اللونية الخفيفة'),
 'action':('#0C2A18','#7FE08D','خلفية الزر الأساسي'), 'on-action':('#FCFBF7','#0C2A18','نص الزر الأساسي'),
 'hero':('#0C2A18','#0C2A18','هيدر الهوية'), 'on-hero':('#FCFBF7','#FCFBF7','نص هيدر الهوية'),
 'hero-muted':('#D6E2D7','#D6E2D7','النص الثانوي فوق الهيدر'), 'success':('#176132','#9BE0AD','نجاح / تأكيد'),
 'success-bg':('#E1F0E2','#173A24','خلفية النجاح'), 'warning':('#725014','#EBCA83','قيد الانتظار'),
 'warning-bg':('#F5EACD','#382D17','خلفية الانتظار'), 'error':('#A12D42','#FFB1BD','خطأ / رفض'),
 'error-bg':('#FBE9ED','#3C1F28','خلفية الخطأ'), 'info':('#315774','#A9CCEB','المعلومة'),
 'info-bg':('#E8EFF5','#1B2C3A','خلفية المعلومة'), 'disabled':('#ECE5D5','#203127','زر غير متاح'),
 'disabled-text':('#626B62','#B2BDB5','نص غير متاح'), 'focus':('#0A5C18','#7FE08D','حلقة التركيز'),
}
GROUPS={'account':'الدخول والتوثيق','tenant':'رحلة المستأجر','shared':'التواصل والمظهر','owner':'مساحة المالك'}

def theme_controls():
    return '<div class="segmented" role="group" aria-label="المظهر">'+''.join(f'<button data-mode="{mode}" aria-pressed="false">{ic(icon)}{label}</button>' for mode,icon,label in [('light','sun','فاتح'),('dark','moon','داكن'),('system','device','حسب الجهاز')])+'</div>'

def toolbar(map_page=False):
    return '<div class="toolbar">'+theme_controls()+('<a class="maplink" href="index.html">العودة إلى الـ٢٠ شاشة</a>' if map_page else '<label>اعرض <select id="group-filter"><option value="all">كل الشاشات · ٢٠</option>'+''.join(f'<option value="{g}">{label}</option>' for g,label in GROUPS.items())+'</select></label><a class="maplink" href="design-map.html">افتح الـDesign Map</a>')+'<span class="theme-label" data-theme-label></span></div>'

def section(s):
    return f'<section class="screen" id="{s["id"]}" data-group="{s["group"]}"><span class="group-label">{GROUPS[s["group"]]}</span><div class="screen-head"><h2><code>{s["id"]}</code>{s["name"]}</h2><button data-open="{s["number"]}">فتح الشاشة</button></div>{s["html"]}<p class="screen-note">{s["note"]}</p><span class="screen-source">{Path(s["source"]).name}</span></section>'

body=f'<div class="atlas"><header class="atlas-intro"><div><h1>هوية واحدة. رحلة كاملة.</h1><p>٢٠ شاشة من سكون، بنفس روح الـlanding page. استكشف الشاشات، بدّل المظهر، وافتح خريطة التصميم كمرجع للتنفيذ.</p><div class="sheet-label">مقترح UI · بيانات توضيحية · ٢٠ شاشة × وضعين</div></div>{wordmark("atlas-signature")}</header>{toolbar()}<div class="gallery">'+''.join(section(s) for s in screens)+'</div><footer class="atlas-footer"><span>كل الأسماء والأسعار والحالات والأرقام توضيحية. التفاعلات محلية داخل المعاينة، وشاشات Flutter لم تُعدّل.</span><a href="DESIGN-MAP.md">مرجع التنفيذ</a><a href="exports/light-overview.png">لوحة الفاتح</a><a href="exports/dark-overview.png">لوحة الداكن</a></footer></div>'

def palette_mapping(old,old_hex,new,new_hex):
    return f'<div class="token-line"><div class="token-side"><i class="swatch" style="background:{old_hex}"></i><span>{old}<small>{old_hex}</small></span></div>{ic("arrow")}<div class="token-side"><i class="swatch" style="background:{new_hex}"></i><span>{new}<small>{new_hex}</small></span></div></div>'

palette='<article class="foundation"><h2>من الـteal<br>إلى أخضر سكون</h2><p>نفس الوظيفة، بمرجع لوني موحّد بين التطبيق والصفحة.</p>'+palette_mapping('teal','#0F766E','accent','#0A5C18')+palette_mapping('off-white','#FAFAF8','sand','#F6F2E9')+palette_mapping('navy','#111827','pine','#0C2A18')+palette_mapping('white','#FFFFFF','paper','#FCFBF7')+'<div class="palette-strip">'+''.join(f'<div><i class="swatch" style="background:{c}"></i>{n}</div>' for n,c in [('pine','#0C2A18'),('brandSoft','#7FE08D'),('brand','#04A417'),('chip','#E1F0E2'),('line','#E3DCCB'),('paper','#FCFBF7')])+'</div><div class="foundation-footer">الأخضر الزاهي #04A417 للتفاصيل الصغيرة. الزر الأساسي في الفاتح pine، وفي الداكن brandSoft بنص pine.</div></article>'
typepanel='<article class="foundation"><h2>خطّان،<br>وإيقاع واحد</h2><p>Readex Pro للعناوين، وIBM Plex Sans Arabic للنصوص والحقول والأزرار.</p><div class="type-sample before"><small>قبل · Tajawal في التطبيق</small><h3>سكنك القادم</h3><small>العينة هنا توضح دور النص؛ ليست عرضًا لخط Tajawal.</small></div><div class="type-sample"><small>بعد · Readex Pro</small><h3>سكنك القادم،<br>من المالك مباشرة.</h3><p style="font-size:11px">تواصل واضح، ومعلومة سهلة القراءة.</p></div><div class="type-scale"><span style="font-size:28px">عنوان</span><span style="font-size:16px">نص</span><span style="font-size:12px">تفاصيل</span></div><div class="foundation-footer">عناوين 24–28 · نص 14–16 · تفاصيل 12–13.<br>محاذاة RTL، وارتفاع سطر 1.5–1.75. لا نصغّر الخط لحل overflow؛ نسمح باللفّ.</div></article>'
identity='<article class="foundation identity-panel"><h2>القوس والتوقيع،<br>بقدر الاستخدام</h2><p>نفس عناصر الـlanding، موزّعة حسب وظيفة الشاشة.</p><div class="identity-examples"><div class="identity-example"><span class="arch"></span><span>القوس في الترحيب</span></div><div class="identity-example"><img src="'+photo+'" alt="عقار داخل قوس"><span>صور حقيقية للعقار</span></div><div class="identity-example">'+signature()+'<span>توقيع خافت في الهيدر</span></div><div class="identity-example"><b>مباشرة.</b>'+badge('موثّق',icon='shield')+'<span>تأكيد لفظي مع الحالة</span></div></div><div class="foundation-footer">الهيدر ثابت الهوية في الوضعين. محتوى العقار والرسائل والنماذج على أسطح هادئة؛ التوقيع لا ينافس النص.</div></article>'
components='<article class="foundation"><h2>أزرار وبطاقات<br>من نفس العيلة</h2><p>قواعد واحدة للمالك والمستأجر، مع ألوان مستقلة للحالات.</p><div class="component-stack">'+btn('إجراء أساسي')+btn('إجراء ثانوي','secondary')+btn('رفض الطلب','destructive')+btn('غير متاح','primary',extra='disabled')+'<div class="component-field">اسم المنطقة أو العقار</div></div><div class="radii-demo">'+''.join(f'<div><div class="radius-shape" style="border-radius:{r}px"></div>{label}</div>' for r,label in [(999,'شرائح 999'),(12,'أزرار 12'),(14,'بطاقات 14')])+'</div><div class="foundation-footer">ارتفاع التحكم 48 على الأقل. مسافات 4 / 8 / 12 / 16 / 24 / 32. حدود هادئة، وأيقونات خطية 20–24، وتركيز مرئي.</div></article>'
foundation=f'<section id="foundations"><h1>الأساسيات: من التطبيق الحالي إلى هوية الصفحة</h1><p class="map-subtitle">خريطة UI مرجعية لسكون · نفس تقسيمة المرجع: ألوان، خطوط، هوية، ومكوّنات.</p><div class="foundation-grid">{palette}{typepanel}{identity}{components}</div></section>'
tokenrows=''.join(f'<tr><td><code>{key}</code></td><td>{label}</td><td><i class="swatch" style="background:{light}"></i><code>{light}</code></td><td><i class="swatch" style="background:{dark}"></i><code>{dark}</code></td></tr>' for key,(light,dark,label) in TOKENS.items())
themeblock='<section class="map-section"><h2>نفس الهوية، في الضوء والليل</h2><p>الصور لا تتعكس ولا تُغمّق بفلاتر. ألوان النص والسطح والإجراء تتبدّل معًا عبر semantic tokens.</p><div class="mode-pair"><div class="mode-example light-sample"><div><h3>الوضع الفاتح</h3><p>ورق دافئ · نص pine</p><button data-mode="light">جرّب الوضع الفاتح</button></div><div><b>سكنك القادم</b><p>خلفية #F6F2E9<br>سطح #FCFBF7<br>نص #0C2A18</p></div></div><div class="mode-example dark-sample"><div><h3>الوضع الداكن</h3><p>أخضر ليلي · نص فاتح</p><button data-mode="dark">جرّب الوضع الداكن</button></div><div><b>سكنك القادم</b><p>خلفية #0A120D<br>سطح #0E1912<br>نص #ECF2EA</p></div></div></div></section>'
statesblock='<section class="map-section"><h2>الحالات جزء من التصميم</h2><div class="state-grid"><article class="state-sample"><h3>تحميل</h3><div class="skeleton" style="height:50px"></div><div class="skeleton"></div><div class="skeleton" style="width:65%"></div><p>هيكل بنفس مساحة المحتوى؛ بدون قفزات.</p></article><article class="state-sample"><h3>قائمة فارغة</h3><p>لسه مفيش عقارات محفوظة.<br>ابدأ البحث واحفظ الأماكن اللي تناسبك.</p>'+btn('استكشف العقارات','primary',5)+'</article><article class="state-sample"><h3>تعذّر التحميل</h3><p>تعذّر تحميل العقارات.<br>راجع اتصالك وحاول مرة ثانية.</p>'+btn('إعادة المحاولة','secondary',action='retry')+'</article><article class="state-sample"><h3>الحالة مكتوبة</h3>'+badge('مؤكدة',icon='check')+' '+badge('بانتظار المالك','warning')+'<div class="gap8"></div>'+badge('مرفوضة','error')+'<p>لا نعتمد على اللون وحده. الحالات تتبع بيانات الـAPI.</p></article></div></section>'
flows=[('الدخول والتوثيق',[(1,'ترحيب'),(2,'دخول'),(3,'OTP'),(4,'توثيق')]),('من البحث للمعاينة',[(5,'الرئيسية'),(6,'النتائج'),(7,'الفلاتر'),(8,'العقار'),(10,'الحجز'),(11,'إرسال'),(12,'المعاينات')]),('إدارة المالك',[(15,'الرئيسية'),(16,'عقاراتي'),(17,'إضافة'),(18,'الطلبات'),(19,'تفاصيل')]),('المحفوظة والمحادثات',[(9,'المحفوظة'),(8,'العقار'),(13,'المحادثات'),(14,'المحادثة')]),('المظهر المشترك',[(20,'حسب الجهاز'),(20,'فاتح'),(20,'داكن')])]
flowblock='<section class="map-section"><h2>خريطة الشاشات والمسارات</h2><p>المجموعات التالية نطاقات مرتبطة، وليست خطوات إجبارية. الدخول الناجح يفتح الرئيسية؛ OTP يظهر في مسار التسجيل أو التحقق الحالي.</p><div class="flow-grid">'+''.join('<div class="flow-group"><h3>'+label+'</h3><div class="flow-links">'+''.join(f'<a href="index.html#S{n:02}">S{n:02} · {t}</a>' for n,t in nodes)+'</div></div>' for label,nodes in flows)+'</div></section>'
rules=[('المظهر','ThemeCubit + ThemePreferences يحفظوا Light / Dark / System؛ الافتراضي System، وإعداد الجهاز يُراقَب أثناء التشغيل.'),('الحركة','320ms مع easeInOutCubic عند التبديل. reduced motion يلغي الحركة، مع الحفاظ على المكان والحقول.'),('التوكنز','التعديل داخل theme extension الخاص بالتطبيق. لا نغيّر ألوان packages/core العامة التي تعتمد عليها تطبيقات أخرى.'),('النصوص','كل نص عبر LocaleKeys / lang.json. Readex للعناوين وIBM Plex لباقي النصوص، مع اختبار العربية والإنجليزية والتكبير.'),('التفاعل','SafeArea وأهداف لمس 48dp، وحالات focus وdisabled وloading وerror، مع دلالات واضحة لقارئ الشاشة.'),('منطق المنتج','التحقق والحجز وحالات الطلب حسب البيانات الحقيقية. إرسال طلب معاينة لا يساوي تأكيد الموعد. الصور والأرقام هنا توضيحية.')]
rulesblock='<section class="map-section"><h2>عقد التنفيذ في Flutter</h2><ul class="implementation-list">'+''.join(f'<li><b>{t}</b><br>{d}</li>' for t,d in rules)+'</ul></section>'
mapbody=f'<div class="map-page">{toolbar(True)}{foundation}{themeblock}<section class="map-section"><h2>جدول الألوان الدلالية</h2><p>حدود الداكن أفتح قليلًا من الـlanding (#294632 بدل #213628) لتمييز الحقول والبطاقات على شاشة الموبايل.</p><table class="token-table"><thead><tr><th>Token</th><th>الاستخدام</th><th>Light</th><th>Dark</th></tr></thead><tbody>{tokenrows}</tbody></table></section>{statesblock}{flowblock}{rulesblock}<footer class="atlas-footer"><span>مرجع مقترح للتنفيذ، مرتبط بملفات التطبيق الحالية. الشاشات والبيانات تمثيلية.</span><a href="design-tokens.json">Design tokens JSON</a><a href="screen-manifest.json">Screen manifest</a></footer></div>'

def embedded_font(name, filename, weights, unicode_range=''):
    raw=base64.b64encode((OUT/'assets'/filename).read_bytes()).decode()
    range_rule=f'unicode-range:{unicode_range};' if unicode_range else ''
    return f'@font-face{{font-family:{name};src:url(data:font/woff2;base64,{raw}) format("woff2");font-weight:{weights};font-display:swap;{range_rule}}}'

fontcss=f'@font-face{{font-family:Plex;src:url({source.font});font-weight:400 600;font-display:swap}}@font-face{{font-family:Plex;src:url({source.bold});font-weight:700 900;font-display:swap}}'+embedded_font('Readex','ReadexPro-Arabic.woff2','160 700','U+0600-06FF,U+0750-077F,U+0870-089F,U+08A0-08FF,U+200C-200E,U+FB50-FDFF,U+FE70-FEFC')+embedded_font('Readex','ReadexPro-Latin.woff2','160 700','U+0000-00FF,U+2000-206F')
fontcss+=f'@font-face{{font-family:Tajawal;src:url({source.data("mobile/packages/core/assets/fonts/Tajawal/Tajawal-Bold.ttf","font/ttf")});font-weight:700;font-display:swap}}'
mapbody=mapbody.replace('العينة هنا توضح دور النص؛ ليست عرضًا لخط Tajawal.','Tajawal الحالي من ملفات التطبيق؛ للمقارنة مع الخط الجديد.')
dialogs='<div class="toast" role="status" hidden></div><dialog class="focus-dialog" aria-label="معاينة الشاشة"><div class="focus-controls"><button data-focus-prev>السابق</button><b data-focus-title></b><button data-focus-next>التالي</button><button data-close-focus aria-label="إغلاق">إغلاق</button></div><div class="focus-body"></div></dialog><dialog class="decision-dialog" aria-labelledby="decision-title"><h3 id="decision-title"></h3><p data-decision-body></p><div class="decision-actions"><button class="primary" data-decision-confirm>تأكيد</button><button class="secondary" data-decision-cancel>رجوع</button></div></dialog>'
init="(()=>{try{let m=new URLSearchParams(location.search).get('theme')||localStorage.getItem('sukoon-proposal-theme')||'system';if(!['light','dark','system'].includes(m))m='system';document.documentElement.dataset.theme=m==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):m}catch{document.documentElement.dataset.theme='light'}})()"
def document(title,content,js=True):
    return f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><script>{init}</script><style>{fontcss}{(OUT/"atlas.css").read_text(encoding="utf-8")}</style></head><body>{content}{dialogs if js else ""}<script>{(OUT/"atlas.js").read_text(encoding="utf-8") if js else ""}</script></body></html>'

if __name__=='__main__':
    assert len(screens)==20
    (OUT/'index.html').write_text(document('سكون · ٢٠ شاشة بهوية واحدة',body),encoding='utf-8')
    (OUT/'design-map.html').write_text(document('سكون · UI Design Map',mapbody),encoding='utf-8')
    (OUT/'screen-manifest.json').write_text(json.dumps([{k:v for k,v in s.items() if k!='html'} for s in screens],ensure_ascii=False,indent=2),encoding='utf-8')
    tokens={k:{'light':l,'dark':d,'usage':u} for k,(l,d,u) in TOKENS.items()}
    tokens['typography']={'display':'Readex Pro','body':'IBM Plex Sans Arabic','displaySizes':[24,28],'bodySizes':[14,16],'metadataSizes':[12,13],'minInteractiveTargetDp':48,'lineHeight':[1.5,1.75]}
    tokens['layout']={'spacing':[4,8,12,16,24,32],'radius':{'control':12,'card':14,'chip':999},'safeArea':True,'prototypeViewport':[350,790]}
    tokens['themePolicy']={'default':'system','persistence':'ThemePreferences / sokoun_theme_mode_v1','transitionMs':320,'curve':'easeInOutCubic','reducedMotion':'no animation','prototypeStorageKey':'sukoon-proposal-theme'}
    (OUT/'design-tokens.json').write_text(json.dumps(tokens,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Built 20 screens, light/dark/system, design map, tokens and screen manifest.')
