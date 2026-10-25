"""Inventory the current sibling Flutter app and build Sprint 1 only. No app writes."""
from pathlib import Path
from html import escape as e
import re, json, hashlib, ast

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
WORKSPACE=BASE.parents[3]
APP=WORKSPACE/'sokoun/apps/sokoun_app/lib'
OUT=HERE/'sprint-01'
OUT.mkdir(exist_ok=True)

def dump(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def resolve(file):
    hits=list(APP.rglob(file))
    if not hits: hits=list((WORKSPACE/'sokoun/packages/core/lib').rglob(file))
    assert len(hits)==1,(file,hits)
    return hits[0]

# These are flow hosts or already represented subpages, not new visual destinations.
aliases={
 'rental_reviews_screen.dart':('reviews_hub_screen.dart','Direct lease-scoped ReviewsHubScreen wrapper; covered as a hub context variant in Sprint 9.'),
 'my_reviews_screen.dart':('reviews_hub_screen.dart','Direct ReviewsHubScreen wrapper without separate UI; reconciled during Sprints 8–10 audit.'),
 'register_flow_screen.dart':('register_screen.dart','Flow host switches between registration and the existing OTP surface.'),
 'profile_screen.dart':('tenant_profile_screen.dart','Workspace dispatcher; tenant and owner profiles are audited separately.'),
 'add_property_basics_page.dart':('owner_property_flow_screen.dart','Basic-information step already represented by original S17.'),
 'owner_listings_screen.dart':('owner_properties_screen.dart','Wrapper directly returns OwnerPropertiesScreen, already represented by original S16; reconciled during Sprint 2 audit.'),
 'promotions_screen.dart':('create_banner_ad_screen.dart','Legacy alias directly opens CreateBannerAdScreen; reconciled in the five-sprint batch.'),
 'view.dart':(None,'Main navigation shell; tabs are inventoried as destinations.'),
 'skeleton_pages.dart':(None,'Passive loading component, not a product destination.'),
}
original=json.loads((BASE/'screen-manifest.json').read_text())
covered={Path(x['source']).name:x['id'] for x in original}
first=[
 ('register_screen.dart','إنشاء حساب','Registration'),
 ('forgot_password_screen.dart','استعادة كلمة المرور','Password recovery'),
 ('kyc_upload_documents_screen.dart','رفع مستندات الهوية','Identity documents'),
 ('kyc_pending_screen.dart','الهوية قيد المراجعة','Identity pending'),
 ('kyc_approved_screen.dart','تم توثيق الحساب','Identity approved'),
 ('tenant_profile_screen.dart','حساب المستأجر','Tenant profile'),
 ('profile_edit_screen.dart','تعديل الملف الشخصي','Edit profile'),
 ('profile_settings_screen.dart','إعدادات الحساب','Account settings'),
 ('profile_verification_screen.dart','حالة توثيق الهوية','Verification status'),
 ('profile_privacy_screen.dart','خيارات الخصوصية','Privacy'),
 ('change_password_screen.dart','تغيير كلمة المرور','Change password'),
 ('email_change_screen.dart','تغيير البريد الإلكتروني','Change email'),
 ('security_sessions_screen.dart','الأجهزة والجلسات','Security sessions'),
 ('language_selection_screen.dart','لغة التطبيق','Language'),
 ('profile_delete_account_screen.dart','حذف الحساب','Delete account'),
 ('profile_contracts_screen.dart','عقودي','Profile contracts'),
 ('notifications_screen.dart','الإشعارات','Notifications'),
 ('notification_detail_screen.dart','تفاصيل الإشعار','Notification detail'),
 ('notification_settings_screen.dart','إعدادات الإشعارات','Notification settings'),
 ('support_screen.dart','مركز المساعدة','Help center'),
]
priority=['shared/auth','shared/profile','owner/profile','tenant/profile','shared/support','shared/public_pages','shared/business_policies','shared/contextual_onboarding','shared/whats_new','shared/recovery','startup','main_view/presentation','tenant/home','tenant/visits','owner/home','owner/properties','owner/visits','shared/property_capture','shared/virtual_tours','tenant/commute','tenant/decision_tools','tenant/ai_assistant','owner/ai_assistant','tenant/premium_alerts','owner/banner_ads','owner/promotions','owner/premium','shared/billing','shared/premium','shared/chat','shared/housing_requests','tenant/housing_requests','owner/housing_demand','shared/rental_interests','tenant/rental_interests','owner/rental_interests','shared/tenancy_invitations','owner/tenancy_invitations','shared/rental_lifecycle','owner/digital_leases','shared/digital_leases','shared/rental_center','shared/rent_management','tenant/rent_management','shared/rental_deposits','shared/rental_handovers','shared/asset_passport','shared/rental_maintenance','shared/rental_disputes','shared/rental_changes','tenant/rental_changes','shared/rental_settlement','owner/rental_payouts','owner/advanced_analytics','shared/reviews','tenant/reviews','tenant/housing_groups','owner/housing_groups','shared/student_housing','shared/company_housing','shared/housing_tenders','shared/living_lab','shared/housing_simulator','shared/transition_network','shared/advanced_execution']
statuses=json.loads((HERE/'sprint-status.json').read_text()) if (HERE/'sprint-status.json').exists() else {'1':'awaiting-review'}
records=[]
for p in sorted(APP.rglob('*.dart')):
    text=p.read_text()
    classes=re.findall(r'class\s+(\w+(?:Screen|Page))\s+extends\s+([\w<>]+)',text)
    if not classes: continue
    rel=p.relative_to(APP)
    parts=rel.parts
    feature='/'.join(parts[1:3]) if parts[0]=='features' and len(parts)>3 else parts[0]
    if p.name=='splash_screen.dart': feature='startup'
    keys=sorted(set(re.findall(r'LocaleKeys\.(\w+)',text)))
    rec=dict(source=str(p.relative_to(WORKSPACE)),file=p.name,classes=[x[0] for x in classes],feature=feature,sha256=hashlib.sha256(text.encode()).hexdigest(),localeKeys=keys,navigationReferences=sorted(set(re.findall(r'\b(\w+(?:Screen|Page))\(',text))-{x[0] for x in classes}))
    if p.name in covered: rec.update(status='original-proposal',proposalId=covered[p.name])
    elif p.name in aliases: rec.update(status='alias-or-component',aliasOf=aliases[p.name][0],reason=aliases[p.name][1])
    else: rec.update(status='planned')
    records.append(rec)
remaining=[r for r in records if r['status']=='planned']
first_names=[x[0] for x in first]
remaining.sort(key=lambda r: (0,first_names.index(r['file'])) if r['file'] in first_names else (1,priority.index(r['feature']) if r['feature'] in priority else 999,r['source']))
for i,r in enumerate(remaining):
    r.update(sprint=i//20+1,proposalId=f'S{i+21:02}',reviewStatus=statuses.get(str(i//20+1),'not-started'))
assert [r['file'] for r in remaining[:20]]==first_names
assert len(covered)==20 and sum(r['status']=='original-proposal' for r in records)==20
inventory=dict(auditDate='2026-10-25',sourceRoot=str(APP.relative_to(WORKSPACE)),method='Concrete classes ending in Screen or Page in app lib; wrappers/components explicitly reconciled. Presentation states and parameter variants are not separate screen counts. Other Dart helpers are not screens.',counts=dict(sourceFiles=len(records),original=20,excluded=sum(r['status']=='alias-or-component' for r in records),remaining=len(remaining),sprints=(len(remaining)+19)//20),screens=records)
dump(HERE/'screen-inventory.json',inventory)
plan=['# Remaining mobile proposal — sprint plan','',f"Audited 2026-10-25 against `{inventory['sourceRoot']}`. {len(records)} screen/page source files: 20 existing proposals, {inventory['counts']['excluded']} reconciled hosts/components, **{len(remaining)} remaining destinations across {inventory['counts']['sprints']} sprints**. Each sprint contains 20; the final sprint contains the remainder.",'','The existing S01–S20 stay intact. Sprint 1 starts at S21. Sprint 1 was approved to continue. Sprints 1–7 were approved to continue. Sprints 8–10 form the current authorized review batch; stop before Sprint 11. No production Flutter implementation is authorized.','', '## Counting and audit scope','',inventory['method'],'','This is a source inventory and scheduling audit for later sprints, not a completed behavioral audit of every later destination. Each future sprint must inspect its screens and dependencies before mockups. Shared generic screens count once; role, public-page, challenge, document and runtime variants must be covered as states during their sprint. Screens need not be public routes to be counted.','']
for i in range(inventory['counts']['sprints']):
    batch=remaining[i*20:(i+1)*20]
    features=list(dict.fromkeys(x['feature'] for x in batch))
    plan += [f'## Sprint {i+1} — '+', '.join(features),'',('**Approved to continue.**' if statuses.get(str(i+1))=='approved-to-continue' else ('**Built in the authorized Sprints 8–10 batch; stop before Sprint 11 for review.**' if 8<=i+1<=10 else '**Built for review; stop here.**') if statuses.get(str(i+1))=='awaiting-review' else '**In progress.**' if statuses.get(str(i+1))=='in-progress' else '**Planned only. Await confirmation of the preceding sprint.**'),'','| ID | Screen | Current Flutter source |','| --- | --- | --- |']
    for r in batch:
        label=next((x[2] for x in first if x[0]==r['file']),r['classes'][0])
        plan.append(f"| {r['proposalId']} | {label} | `{r['source']}` |")
    plan.append('')
plan+=['## Reconciled hosts and components','','| File | Treatment |','| --- | --- |']+[f'| `{k}` | {v[1]} |' for k,v in aliases.items()]
plan+=['','## Delivery gate','','After each sprint: 20 distinct mockups (or the final remainder), Light/Dark/System, source-linked behavior notes, explicit important states, visual review, and local interaction checks. The current authorization covers Sprints 8–10 together. Stop for user review before Sprint 11.','', 'Sprint 2: [Open mockups](sprint-02/index.html) · [Behavior audit](sprint-02/AUDIT.md). Sprint 1: [Open mockups](sprint-01/index.html) · [Behavior audit](sprint-01/AUDIT.md). Existing foundation: [Design Map](../design-map.html).']
(HERE/'SPRINT-PLAN.md').write_text('\n'.join(plan)+'\n')

# Borrow the exact embedded fonts, foundation palette and authentic signature from the completed atlas.
old=(BASE/'original-twenty.html').read_text()
shared_style=re.search(r'<style>(.*?)</style>',old,re.S).group(1)
logo=re.search(r'<svg class="atlas-signature".*?</svg>',old,re.S).group(0)
icons={
 'heart':'<path d="M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8-1c-4 5 8 15 8 15S24 10 20 5Z"/>','arrow':'<path d="m9 5 7 7-7 7"/>','user':'<circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/>',
 'shield':'<path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6Z"/><path d="m8 12 3 3 5-6"/>',
 'mail':'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3 6 9 7 9-7"/>',
 'lock':'<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>','file':'<path d="M14 2H5v20h14V7Zm0 0v5h5M8 12h8m-8 4h6"/>',
 'bell':'<path d="M5 17h14l-2-3V9a5 5 0 0 0-10 0v5Zm5 3h4"/>',
 'device':'<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/>',
 'help':'<circle cx="12" cy="12" r="9"/><path d="M9 8a3 3 0 0 1 6 0c0 2-3 2-3 5m0 3h.01"/>',
 'globe':'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
 'check':'<path d="m5 12 4 4L19 6"/>','camera':'<path d="M3 7h4l2-3h6l2 3h4v14H3Z"/><circle cx="12" cy="14" r="4"/>',
 'home':'<path d="m2 11 10-8 10 8M5 9v12h14V9m-10 12v-7h6v7"/>',
 'search':'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>','chat':'<path d="M3 3h18v14H8l-5 4Zm4 5h10M7 12h7"/>',
 'settings':'<path d="M3 7h18M3 17h18"/><circle cx="8" cy="7" r="3"/><circle cx="16" cy="17" r="3"/>',
 'trash':'<path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>',
 'eye':'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
}
# Read the original icon registry as data without running the old Windows builder.
for original_builder, prefix, suffix in [('build_proposal.py','paths = ','\ndef icon'),('build_atlas.py','source.paths.update(',')\nic =')]:
    registry=(BASE/original_builder).read_text().split(prefix,1)[1].split(suffix,1)[0].strip()
    icons.update(ast.literal_eval(registry))

def icon(name):return f'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icons[name]}</svg>'
def button(text,to=None,action=None,kind='primary',extra=''):
    attr=f'data-go="{to}"' if to else f'data-action="{action or "preview"}"'
    return f'<button type="button" class="{kind}" {attr} {extra}>{text}</button>'
def row(text,sub='',to=None,ico='arrow',action=None):
    return button(f'<span class="row-icon">{icon(ico)}</span><span class="grow"><b>{text}</b>{f"<small>{sub}</small>" if sub else ""}</span>{icon("arrow")}',to,action,'menu-row')
def field(label,value='',kind='text',name='',hint='',extra=''):
    input=f'<input name="{name}" type="{kind}" value="{e(value)}" placeholder="{e(hint)}" {extra}>'
    if kind=='password':input=f'<div class="password-wrap">{input}{button(icon("eye"),action="password",kind="eye-button",extra="aria-label=إظهار-كلمة-المرور")}</div>'
    return f'<label class="field"><span>{label}</span>{input}</label>'
def note(text,kind='info',ico='shield'):return f'<div class="notice {kind}">{icon(ico)}<p>{text}</p></div>'
def panel(content,cls=''):return f'<div class="panel {cls}">{content}</div>'
def section(title,content):return f'<h3 class="group-title">{title}</h3>{panel(content)}'
def summary(rows):return '<div class="summary">'+''.join(f'<div class="summary-row"><span>{a}</span><b>{b}</b></div>' for a,b in rows)+'</div>'
def intro(title,sub,ico=None):return f'<div class="intro">{f"<span class=emblem>{icon(ico)}</span>" if ico else ""}<h2>{title}</h2><p>{sub}</p></div>'
def badge(text,kind=''):return f'<span class="badge {kind}">{text}</span>'
def switch(title,sub,key,on=True,locked=False):
    return f'<div class="switch-row"><span class="grow"><b>{title}</b><small>{sub}</small></span><button type="button" role="switch" aria-label="{title}" aria-checked="{str(on).lower()}" data-switch="{key}" {"disabled" if locked else ""}><span></span></button></div>'
def footer(text,action=None,to=None,kind='primary',extra=''):return f'<footer class="actions">{button(text,to,action,kind,extra)}</footer>'
def nav():
    items=[('home','الرئيسية','S05'),('heart','المحفوظة','S09'),('chat','الرسائل','S13'),('home','مسكني',None),('user','حسابي','S26')]
    return '<nav class="nav">'+''.join(button(icon(i)+f'<span>{t}</span>',to,action='my-housing' if to is None else None,kind='active' if i=='user' else '') for i,t,to in items)+'</nav>'
def otp():return '<div class="otp-row" dir="ltr">'+''.join(f'<input aria-label="رقم الرمز {i+1}" inputmode="numeric" maxlength="1" pattern="[0-9٠-٩]" required>' for i in range(6))+'</div>'

screens=[]
def add(index,content,rule,states,dependencies=(),back='S26',footer_html='',group='account',variants=None):
    filename,ar,en=first[index]
    r=next(x for x in remaining if x['file']==filename)
    dep=[]
    for f in dependencies:
        p=resolve(f); txt=p.read_text();dep.append(dict(source=str(p.relative_to(WORKSPACE)),sha256=hashlib.sha256(txt.encode()).hexdigest(),localeKeys=sorted(set(re.findall(r'LocaleKeys\.(\w+)',txt)))))
    screens.append(dict(id=r['proposalId'],name=ar,english=en,source=r['source'],sha256=r['sha256'],group=group,behavior=rule,requiredStates=states,dependencies=dep,back=back,content=content,footer=footer_html,variants=variants or {}))

add(0,intro('أول خطوة لبيتك الجاي.','حساب واحد لرحلتك مع سكون.')+'<form data-form="register">'+field('الاسم الأول',name='first',hint='اسمك الأول',extra='required autocomplete="off"')+field('اسم العائلة',name='last',hint='اسم العائلة',extra='required autocomplete="off"')+field('رقم الهاتف',name='phone',hint='01xxxxxxxxx',extra='required pattern="01[0125][0-9]{8}" inputmode="tel" dir="ltr"')+field('البريد الإلكتروني',kind='email',name='email',hint='name@example.com',extra='required dir="ltr" autocomplete="off"')+field('كلمة المرور',kind='password',name='password',extra='required minlength="8" autocomplete="new-password"')+field('تأكيد كلمة المرور',kind='password',name='confirm',extra='required minlength="8" autocomplete="new-password"')+'<p class="small muted">٨ أحرف على الأقل. لا تستخدم كلمة مرور مكوّنة من مسافات فقط.</p><button class="primary wide" type="submit">إنشاء حساب</button></form>'+button('عندك حساب؟ سجّل الدخول',to='S02',kind='textbtn wide'),
 'Separate first/last names, Egyptian mobile, email, password and confirmation. RegisterFlowScreen submits registration then shows email OTP; successful verification returns to login. Do not route registration directly to KYC or mark identity verified.', ['empty','invalid','submitting','server-error','otp-next'], ['register_flow_screen.dart','register_intro.dart','credential_validators.dart'],back='S01')
add(1,intro('نسيانها وارد.','اكتب بريد حسابك، وهنبعت لك رابط استعادة كلمة المرور.','lock')+'<form data-form="recovery">'+field('البريد الإلكتروني',kind='email',name='email',hint='name@example.com',extra='required dir="ltr"')+'<button class="primary wide" type="submit">إرسال رابط الاستعادة</button></form>'+note('الرابط يصل إلى بريدك. لا تشاركه مع أي شخص.','info','mail')+button('الرجوع لتسجيل الدخول',to='S02',kind='textbtn wide'),
 'Email reset link, not an OTP password-reset flow. Mask sent-to address, allow changing email and resending; display authoritative server messages and cooldown.', ['empty','invalid','sending','sent','server-error'], ['forgot_password_form.dart','forgot_password_sent_view_content.dart'],back='S02')
add(2,'<div class="step-caption"><span>توثيق الحساب</span><span>٢ من ٢</span></div><div class="steps"><span class="done"></span><span class="done"></span></div>'+intro('صورة أوضح. ثقة أكبر.','جهّز صورة واضحة لكل مستند.')+field('الرقم القومي',name='nationalId',hint='١٤ رقمًا',extra='inputmode="numeric" maxlength="14" dir="ltr"')+''.join(button(icon(ic)+f'<span><b>{t}</b><small>اضغط لاختيار صورة واضحة</small></span><span class="upload-state">＋</span>',action='sample-upload',kind='upload-tile',extra=f'data-document="{k}"') for ic,t,k in [('file','الوجه الأمامي للبطاقة','front'),('file','الوجه الخلفي للبطاقة','back'),('camera','صورة شخصية','selfie')])+note('مستنداتك لمراجعة الهوية، ولا تظهر في ملفك العام.')+'<div class="inline-feedback" aria-live="polite"></div>',
 'Audit mismatch: widgets label some existing-account inputs optional and canSubmit permits blank ID, but _submit always calls MediaValidators.validateKycDocuments, which requires a valid Egyptian national ID and all three images. Proposal follows the executed validator, flags the copy mismatch; no invented optional bypass. Preserve unsaved changes and file limits.', ['empty','selected','invalid','uploading','permission-denied','server-error','pending'], ['kyc_upload_documents_view.dart','kyc_upload_documents_data.dart','kyc_document_picker.dart','media_validators.dart'],back='S04',footer_html=footer('إرسال للمراجعة','submit-kyc'))
add(3,intro('وصلت مستنداتك.','طلب توثيق الهوية قيد المراجعة. هنحدّث حالته بعد انتهاء المراجعة.','clock')+badge('قيد المراجعة','warning')+summary([('الاسم','أحمد محمود'),('تاريخ الإرسال','٢٥ أكتوبر ٢٠٢٦')])+note('طلبك قيد المراجعة. تقدر تتابع حالته من حسابك.','info','clock'),
 'Pending is not approved. Name, submittedAt and expectedReviewTime render only when present. OK returns existing accounts to initial route; new registration returns to login.', ['pending','metadata-absent','existing-account'], ['kyc_status_summary_card.dart'],back='S29',footer_html=footer('حسنًا',to='S26'))
add(4,intro('أهلًا بثقة أكبر.','تمت مراجعة هويتك والموافقة على توثيق حسابك.','shield')+badge('حساب موثّق')+section('جاهز لخطوتك الجاية',row('التواصل داخل سكون','شارة التوثيق ترافق حسابك',ico='chat',action='preview')+row('البحث عن سكن','ابدأ استكشاف العقارات',to='S06',ico='home')),
 'Render approved only from authoritative verification result. Current KycApprovedScreen primary navigation is TenantSearchScreen; preserve entitlement decisions in app/server rather than granting capabilities from prototype.', ['approved'], ['kyc_feature_tile.dart'],back='S29',footer_html=footer('ابدأ البحث عن سكن',to='S06'))
profile=panel('<div class="profile-hero"><span class="avatar big">أ</span><h2>أحمد محمود</h2><p>حساب المستأجر</p>'+button('تعديل الملف',to='S27',kind='secondary')+'</div>','arch-panel')+row('توثيق الهوية','حساب موثّق',to='S29',ico='shield')+section('رحلتك مع سكون',row('عقودي','عقودك ومستندات الإيجار',to='S36',ico='file')+row('تقييماتي','مراجعاتك وتجاربك السابقة',action='my-reviews',ico='shield')+row('ملخص الحساب','عرض نشاط الحساب',action='account-summary',ico='user'))+section('بيانات الحساب',summary([('الاسم','أحمد محمود'),('البريد الإلكتروني','ahmed@example.com')]))
add(5,profile,'ProfileScreen dispatches workspace; this mockup represents TenantProfileScreen, not owner/company variants. Keep API-driven account details, activity and menu visibility, refresh after edits; preserve five individual-workspace tabs (home, saved, messages, housing, profile); company workspace has different activity entry.', ['loaded','loading','empty','server-error','unverified'], ['profile_screen.dart','tenant_profile_content_view.dart','profile_content_view.dart','tenant_profile_actions.dart','home_tab.dart'],footer_html=nav(),group='profile')
add(6,'<div class="profile-hero"><button class="avatar big" data-action="avatar" aria-label="تغيير الصورة">أ</button><p>تغيير صورة الملف</p></div><form data-form="profile">'+field('الاسم الكامل','أحمد محمود',name='name',extra='required')+field('البريد الإلكتروني','ahmed@example.com',kind='email',extra='readonly dir="ltr"')+button('تغيير البريد الإلكتروني',to='S32',kind='textbtn')+'<label class="field"><span>المدينة</span><select name="city"><option>القاهرة</option><option>الجيزة</option><option>بدون مدينة</option></select></label><button class="primary wide" type="submit">حفظ التغييرات</button></form>',
 'Editable full name, avatar and city. Email is read-only with separate email-change flow. Preserve draft on failed save, server-known details on load failure and unsaved-changes guard. Save/refresh only after successful response.', ['loaded','dirty','saving','saved','load-error','server-error'], ['profile_editor_scaffold.dart','profile_account_fields.dart'],back='S26',group='profile')
settings=note('اختيارات تناسبك، وحماية لحسابك.','info','settings')+section('الاشتراكات والفواتير',row('اشتراكاتي',ico='file',action='subscriptions')+row('فواتيري',ico='file',action='invoices'))+section('التفضيلات',row('المظهر','حسب الجهاز',to='S20',ico='device')+row('اللغة','العربية',to='S34',ico='globe')+row('الإشعارات',to='S39',ico='bell'))+section('الأمان',row('مراجعات سياسة المحادثات',action='chat-policy',ico='chat')+row('الأجهزة والجلسات',to='S33',ico='device')+row('خيارات الخصوصية',to='S30',ico='shield')+row('تغيير كلمة المرور',to='S31',ico='lock'))+section('المعلومات والمساعدة',row('الشروط والخصوصية',action='legal',ico='file')+row('سياسات الاستخدام',action='business-policies',ico='file')+row('إرشادات التجربة',action='guide-settings',ico='help')+row('مركز المساعدة',to='S40',ico='help'))+button('تسجيل الخروج',action='logout',kind='secondary wide')+button('حذف الحساب',to='S35',kind='danger-text wide')
add(7,settings,'Preserve billing visibility (!workspace.isCompany), preference routes, security, public pages, experience guide and business policies. Logout and delete remain separate confirmed operations. Company/owner copy and visibility use workspace.', ['loaded','owner','company'], ['profile_settings_content_view.dart','profile_logout_sheet.dart'],back='S26',group='profile')
verify=intro('هويتك موثّقة.','تمت الموافقة على توثيق حسابك.','shield')+badge('تمت الموافقة')+summary([('الاسم','أحمد محمود'),('تاريخ الإرسال','٢٥ أكتوبر ٢٠٢٦')])+note('شارة التوثيق تخص الهوية، وحالة ملكية العقار تُعرض بشكل منفصل.')
add(8,verify,'Status comes from ProfileVerificationContent: approved, pending, rejected, incomplete, unknown. Show rejection reason when present. Upload action only for canSubmit; refresh after returning from KycIntroScreen.', ['approved','pending','rejected','incomplete','unknown','loading','server-error'], ['profile_verification_content_view.dart'],back='S26',group='profile',variants={
 'pending':intro('قيد المراجعة.','مستنداتك وصلت، والمراجعة لم تكتمل بعد.','clock')+badge('بانتظار المراجعة','warning'),
 'rejected':intro('محتاجين صورة أوضح.','راجع سبب الرفض قبل إعادة إرسال المستندات.','shield')+note('سبب توضيحي من الخادم: صورة الوجه الخلفي غير واضحة.','error','file')+button('إعادة رفع المستندات',to='S23',kind='primary wide'),
 'incomplete':intro('كمّل توثيق هويتك.','ارفع مستنداتك لبدء المراجعة.','shield')+button('رفع المستندات',to='S23',kind='primary wide'),
 'unknown':intro('الحالة غير متاحة.','تعذّر تحديد حالة التوثيق. أعد تحديث البيانات.','help')+button('تحديث الحالة',action='reset-state',kind='secondary wide')})
add(9,intro('خصوصيتك، باختيارك.','اختيارات واضحة لظهورك ومشاركة موقعك.','shield')+panel(switch('مشاركة الموقع','السماح بمشاركة الموقع وفق إعداد حسابك.','location',False)+switch('ظهور الملف في البحث','السماح بعرض ملفك ضمن نتائج البحث.','search',True))+note('التواصل الآمن يظل داخل سكون. أذونات الجهاز تُدار من إعدادات الجهاز.')+'<p class="small muted">تقدر تغيّر اختيارات الخصوصية في أي وقت.</p>',
 'Only shareLocation and showProfile from server settings values. Per-toggle pending; preserve/restore baseline on failure. Do not invent phone disclosure switches or treat sharing preference as OS permission.', ['loaded','saving','server-error','empty'], ['profile_privacy_content_view.dart'],back='S28',group='security')
add(10,intro('جدّد حماية حسابك.','بعد تغيير كلمة المرور بنجاح، هتحتاج تسجّل دخولك من جديد.','lock')+'<form data-form="password">'+field('كلمة المرور الحالية',kind='password',name='current',extra='required')+field('كلمة المرور الجديدة',kind='password',name='password',extra='required minlength="8"')+field('تأكيد كلمة المرور الجديدة',kind='password',name='confirm',extra='required minlength="8"')+note('استخدم كلمة مرور من ٨ أحرف على الأقل، وتجنب مشاركتها.','info','lock')+'<button class="primary wide" type="submit">حفظ كلمة المرور</button></form>',
 'Current/new/confirmation fields; same credential policy as app validator. Preserve unsaved-changes guard. Successful save stops notification device registration and logs out; never return with a still-authenticated success.', ['empty','invalid','saving','server-error','reauthenticate'], ['change_password_form.dart','credential_validators.dart'],back='S28',group='security')
email_default=intro('بريد جديد. نفس الأمان.','نأكد بريدك الحالي، ثم نأكد البريد الجديد قبل التغيير.','mail')+'<ol class="timeline"><li>تأكيد البريد الحالي</li><li>إدخال البريد الجديد</li><li>تأكيد البريد الجديد</li></ol>'+note('عنوانك الحالي: ah****@example.com','info','lock')+button('ابدأ تأكيد البريد الحالي',action='email-start',kind='primary wide')
email_enter=intro('بريدك الجديد.','اختر عنوان البريد الذي تريد استخدامه.','mail')+'<form data-form="new-email">'+field('البريد الجديد',kind='email',name='email',hint='new@example.com',extra='required dir="ltr"')+'<button class="primary wide" type="submit">متابعة</button></form>'
email_old=intro('أكد بريدك الحالي.','أدخل رمزًا من ٦ أرقام أُرسل إلى ah****@example.com.','mail')+'<form data-form="email-old">'+otp()+'<button class="primary wide" type="submit">تأكيد البريد الحالي</button></form>'+button('إعادة الإرسال',action='resend',kind='textbtn wide')
email_new=intro('أكد بريدك الجديد.','أدخل الرمز المرسل إلى بريدك الجديد.','mail')+'<form data-form="email-new">'+otp()+'<button class="primary wide" type="submit">تأكيد التغيير</button></form>'+button('إعادة الإرسال',action='resend',kind='textbtn wide')
add(11,email_default,'Start → verify_old (shared 6-digit OTP challenge) → enter_new → verify_new → complete. Authoritative resendAt, status recovery, expired/restart; only update local user after server complete, retain server email if local cache write fails.', ['start','verify-old','enter-new','verify-new','expired','server-error','complete'], ['email_change_form.dart','email_change_recovery_actions.dart'],back='S27',group='security',variants={'verify-old':email_old,'enter-new':email_enter,'verify-new':email_new,'expired':note('انتهت صلاحية التحدي. راجع حالة العملية قبل البدء من جديد.','warning','clock')+button('مراجعة الحالة',action='email-status',kind='secondary wide')+button('ابدأ من جديد',action='email-restart',kind='primary wide'),'complete':intro('تم تغيير البريد.','تم اعتماد العنوان الجديد بنجاح.','check')+button('العودة للملف',to='S27',kind='primary wide')})
add(12,intro('اعرف مين متصل.','راجع الأجهزة اللي دخلت إلى حسابك.','device')+panel('<div class="session-card">'+badge('الجلسة الحالية')+'<h3>iPhone · القاهرة</h3><p>آخر نشاط: الآن · بيانات توضيحية</p>'+button('إنهاء الجلسة الحالية',action='revoke-current',kind='textbtn')+'</div>')+panel('<div class="session-card"><h3>Chrome · Windows</h3><p>آخر نشاط: ٢٤ أكتوبر · بيانات توضيحية</p>'+button('إنهاء الجلسة',action='revoke-session',kind='textbtn')+'</div>')+button('إنهاء الجلسات الأخرى',action='revoke-others',kind='secondary wide')+button('إنهاء كل الجلسات',action='revoke-all',kind='secondary wide')+button('الإبلاغ عن اختراق الحساب',action='compromised',kind='danger-text wide')+note('لو لاحظت جهازًا غريبًا، أنهِ جلسته وراجع حماية حسابك.'),
 'Distinct confirmed revoke-one, others, all, compromise. Other session revocation reloads; current/all/compromised stops device notifications and logs out only after successful write. Keep no-session/read failure states.', ['loaded','confirming','saving','empty','server-error','reauthenticate'], ['security_sessions_body.dart'],back='S28',group='security')
add(13,intro('باللغة اللي تريحك.','اختار لغة عرض التطبيق.','globe')+'<fieldset class="language-options"><legend class="sr-only">لغة التطبيق</legend><label><input type="radio" name="language" value="ar" checked><span><b>العربية</b><small>Arabic</small></span></label><label><input type="radio" name="language" value="en"><span><b>English</b><small>الإنجليزية</small></span></label></fieldset>'+note('سيُطبّق اتجاه الواجهة مع اللغة المختارة.','info','globe'),
 'Arabic and English selection; explicit confirm persists via Languages. This Arabic visual proposal demonstrates selection/confirmation only, not a fabricated complete English translation.', ['arabic','english-selected','saving','server-error'], ['language_selection_options.dart'],back='S28',group='profile',footer_html=footer('تأكيد اللغة','language-confirm'))
add(14,intro('قبل ما تودّع سكون.','حذف الحساب إجراء نهائي. راجع أثر القرار على بياناتك.','trash')+note('سيتم حذف الحساب والبيانات المرتبطة وفق سياسة الخدمة.','error','trash')+section('ماذا يشمل الحذف؟','<ul class=consequences><li>بيانات الهوية والحساب</li><li>الإعلانات المرتبطة بالحساب</li><li>النشاط داخل سكون</li></ul>')+'<label class="ack"><input type="checkbox" name="ack">أفهم أن حذف الحساب نهائي وأوافق على المتابعة.</label>',
 'Acknowledgement checkbox gates delete. Preserve server refusal and message, lock back during submission. Only successful delete triggers device-notification stop and logout. Prototype never deletes or collects real credentials.', ['unchecked','acknowledged','saving','server-error','deleted'], ['profile_deletion_content.dart'],back='S28',group='security',footer_html=footer('حذف الحساب نهائيًا','delete-account',kind='danger',extra='disabled'))
add(15,intro('اتفاقاتك في مكان واحد.','راجع عقود الإيجار ومستنداتها.','file')+panel(badge('عقد نشط')+'<h3>شقة المعادي</h3><p class="small muted">رقم العقد · مثال ١٠٢٤</p>'+summary([('بداية العقد','١ نوفمبر ٢٠٢٦'),('نهاية العقد','٣١ أكتوبر ٢٠٢٧')])+button('فتح مستند العقد',action='contract-document',kind='secondary wide'))+section('متابعة السكن',row('مسكني','إدارة رحلة الإيجار',action='my-housing',ico='home')),
 'Paginated server contracts; statuses active/expired/cancelled/unknown; document link is validated and can be unavailable. Preserve workspace-specific journey entries. Owner rentals/leases/finance and tenancy invitations belong to later destinations.', ['loaded','loading','empty','server-error','document-unavailable'], ['profile_contracts_list.dart','profile_contract_card.dart','contracts_journey_actions.dart'],back='S26',group='profile')
add(16,button('تحديد الكل كمقروء',action='read-all',kind='textbtn wide')+'<h3 class="group-title">اليوم</h3>'+''.join(button(f'<span class="row-icon">{icon(ic)}</span><span class="grow"><b>{t}</b><small>{sub}</small><small>{time}</small></span><span class="unread-dot" aria-label="غير مقروء"></span>',to='S38',kind='notification-card') for ic,t,sub,time in [('clock','طلب المعاينة قيد الانتظار','طلبك وصل إلى المالك، وفي انتظار قراره.','منذ ١٠ دقائق'),('chat','رسالة جديدة','لديك رسالة داخل سكون.','منذ ساعة'),('file','مستند جديد','يوجد تحديث على مستندات الإيجار.','أمس')])+button('إعدادات الإشعارات',to='S39',kind='secondary wide'),
 'Role-resolved paginated inbox, unread count, mark-one/read-all with rollback and account-session guard. Detail fetches authoritative data; related destination is validated, not an arbitrary push URL. Invoice shortcut preserved when available.', ['loaded','loading','empty','marking','server-error'], ['notifications_screen_content.dart','notification_destination.dart'],back='S26',group='notifications')
add(17,intro('طلبك وصل للمالك.','طلب المعاينة في انتظار الموافقة.','clock')+badge('بانتظار المالك','warning')+'<p class="detail-message">أرسلنا طلب معاينة شقة المعادي. الموعد لا يُعتبر مؤكدًا حتى يقبل المالك الطلب.</p>'+summary([('العقار','شقة المعادي'),('نوع التحديث','طلب معاينة'),('تاريخ الإشعار','٢٥ أكتوبر ٢٠٢٦')])+note('تابع حالة الطلب من صفحة المعاينات. هنبلغك بأي تحديث.','info','bell')+button('عرض الطلب المرتبط',action='notification-related',kind='primary wide')+button('إغلاق',to='S37',kind='textbtn wide'),
 'Load detail, preserve primary destination from validated notification data and role. Dismiss returns; do not convert pending request into confirmed visit. Related content may be unavailable/unauthorized/deleted.', ['loaded','loading','server-error','destination-unavailable'], ['notification_details_content.dart','notification_navigation.dart'],back='S37',group='notifications')
add(18,panel('<div class="row spread"><b>إشعارات الجهاز</b>'+badge('مسموح')+'</div><p class="small muted">إذن الجهاز يُدار بشكل مستقل.</p>'+button('فتح إعدادات الجهاز',action='device-settings',kind='textbtn'))+section('اختيارات الإشعارات',switch('طلبات المعاينة','تحديثات الطلبات والمواعيد.','visits')+switch('الرسائل الجديدة','الرسائل داخل سكون.','messages')+switch('تحديثات العقارات','جديد العقارات التي تتابعها.','properties')+switch('التنبيهات الأمنية','حماية حسابك. لا يمكن تغيير هذا الخيار حاليًا.','security',True,True)+switch('العروض والتحديثات','أخبار ومزايا سكون.','promotions',False))+note('اختيارات الإشعارات مستقلة عن إذن الجهاز. راجع الإذن إذا لم تصلك التنبيهات.','info','bell'),
 'Server-driven items, canChange and footerNote; five known fallback keys. Demonstrated locked security alert is illustrative, not a hardcoded rule. Per-key optimistic preference with baseline recovery; device permission separate.', ['loaded','saving','server-error','permission-denied','empty'], ['notification_settings_content.dart','device_notification_permission_tile.dart'],back='S37',group='notifications')
faq='<label class="field"><span>ابحث في المساعدة</span><input data-faq-search placeholder="اكتب سؤالك…" type="search"></label>'
for q,a in [('إزاي أتابع طلب معاينة؟','افتح المعاينات لمراجعة الحالة. الطلب يظل في الانتظار حتى يوافق المالك.'),('إزاي أتابع توثيق هويتي؟','من حسابي، افتح توثيق الهوية للاطلاع على الحالة وسبب الرفض إن وُجد.'),('فين أراجع العقود؟','افتح عقودي من حسابك لعرض المستندات المتاحة.')]:faq+=f'<details class="faq"><summary>{q}</summary><p>{a}</p></details>'
add(19,intro('موجودين عشان نساعدك.','ابحث عن إجابة، أو تابع طلب دعم.','help')+button('طلب دعم جديد',action='support-new',kind='primary wide')+button('طلباتي السابقة',action='support-tickets',kind='secondary wide')+button('اقترح تحسينًا',action='feedback',kind='textbtn wide')+section('الأسئلة الشائعة',faq)+'<p data-faq-empty hidden>لا توجد إجابة مطابقة. جرّب كلمات أخرى.</p>'+button('راسل فريق الدعم بالبريد',action='support-email',kind='textbtn wide'),
 'Workspace/language-scoped remote help, FAQ search and empty results; support new/tickets/feedback are separate next-sprint destinations. Email contact only if backend supplies a valid address. FAQ content here is illustrative.', ['loaded','loading','server-error','empty','no-search-results','contact-unavailable'], ['support_help_header.dart','support_help_content_view.dart'],back='S26',group='support')

# Visual correction requested after review: extend the original screen families directly.
wordmark=logo.replace('class="atlas-signature"','class="auth-mark"')
signature=re.search(r'<svg class="signature".*?</svg>',old,re.S).group(0)
status_chrome=re.search(r'<div class="status\s*">.*?</div>',old,re.S).group(0).replace('class="status "','class="status"')
references={
 'S21':['S02','S17'],'S22':['S02'],'S23':['S04','S17'],
 'S24':['S03','S19'],'S25':['S03','S04'],'S26':['S05','S18'],
 'S27':['S17','S19'],'S28':['S20'],'S29':['S03','S19'],
 'S30':['S20'],'S31':['S02','S17'],'S32':['S02','S03'],
 'S33':['S18','S20'],'S34':['S20'],'S35':['S20','S19'],
 'S36':['S18','S19'],'S37':['S05','S18'],'S38':['S19'],
 'S39':['S20'],'S40':['S05','S18'],
}
hubs={
 'S26':('أحمد محمود','حساب المستأجر'),
 'S37':('كل جديد،<br>في مكانه.','تحديثات رحلتك مع سكون.'),
 'S40':('معاك،<br>في كل خطوة.','إجابة واضحة، وخطوة تطمّنك.'),
}
for screen in screens:
    sid=screen['id']
    screen['visualReference']=references[sid]
    screen['layout']='hub' if sid in hubs else ('auth' if sid in ['S21','S22','S32'] else 'status' if sid in ['S24','S25','S29','S38'] else 'utility')
    for key in ['content',*screen['variants']]:
        html=screen['content'] if key=='content' else screen['variants'][key]
        # No new arch badges: status symbols use the original S03 circular treatment.
        if screen['layout']=='status' or (sid=='S32' and key in ['verify-old','verify-new','complete']):
            html=html.replace('<span class=emblem>','<span class="empty-symbol">')
            html=html.replace('<div class="intro">','<div class="intro auth-intro center">')
            html=re.sub(r'(<span class="empty-symbol">.*?</svg>)</span>',r'\1</span>',html,flags=re.S)
        else:
            html=re.sub(r'<span class=emblem>.*?</span>','',html,flags=re.S)
            html=html.replace('<div class="intro">','<div class="intro auth-intro">')
        if screen['layout']=='auth' and (key=='content' or key in ['enter-new']): html=wordmark+html
        if key=='content':screen['content']=html
        else:screen['variants'][key]=html
    if sid=='S21':
        screen['content']=screen['content'].replace('أول خطوة لبيتك الجاي.','أول خطوة،<br>لبيتك الجاي.')
        # The original S17 uses paired fields for related short values.
        screen['content']=re.sub(r'(<label class="field">.*?</label>)(<label class="field">.*?</label>)',r'<div class="field-pair">\1\2</div>',screen['content'],count=1,flags=re.S)
    if sid=='S23':screen['content']=screen['content'].replace('صورة أوضح. ثقة أكبر.','صورة أوضح.<br>ثقة أكبر.')
    if sid in ['S24','S25','S29','S38']:
        screen['content']=re.sub(r'(?<=</div>)(<span class="badge[^>]*>.*?</span>)',r'<div class="center">\1</div>',screen['content'],count=1,flags=re.S)
    if sid=='S26':
        screen['content']=screen['content'].split('</div></div>',1)[1]
    if sid=='S28':
        screen['content']=re.sub(r'^<div class="notice.*?</div>','<div class="auth-intro"><h2>حسابك، على راحتك.</h2><p>تفضيلاتك وأمانك في مكان واحد.</p></div>',screen['content'],count=1,flags=re.S)
    if sid in ['S37','S40']:
        screen['content']=re.sub(r'^<div class="intro.*?</div>','',screen['content'],count=1,flags=re.S)
    if sid in hubs:
        title,subtitle=hubs[sid]
        brandmark=logo.replace('class="atlas-signature"','class="wordmark"')
        header_action=button(icon('settings'),to='S39' if sid=='S37' else 'S28',kind='iconbtn',extra='aria-label="الإعدادات"')
        avatar_html='<span class="avatar">أ</span>' if sid=='S26' else ''
        screen['header']=f'<header class="brandhead">{signature}<div class="brandrow">{button(icon("arrow"),to=screen["back"],kind="iconbtn",extra="aria-label=رجوع")}{brandmark}{avatar_html}{header_action}</div><h2>{title}</h2><p>{subtitle}</p>{button("تعديل الملف",to="S27",kind="brand-edit") if sid=="S26" else ""}</header>'
    else:
        screen['header']=f'<header class="topbar">{button(icon("arrow"),screen["back"],kind="iconbtn",extra="aria-label=رجوع")}<h2>{screen["name"]}</h2></header>'

assert len(screens)==20
manifest=[{k:v for k,v in s.items() if k not in ['content','footer','variants','header']}|{'renderedVariants':list(s['variants'])} for s in screens]
dump(OUT/'screen-manifest.json',manifest)
audit=['# Sprint 1 — source and behavior audit','','S21–S40. Audited against the sibling `sokoun` code on 2026-10-25. The original S01–S20 and foundation remain unchanged. All names, statuses, notification content and device data are illustrative. No external operations occur.','','## Material source findings','','- Registration currently proceeds to email OTP then login, not directly to identity approval.','- KYC has inconsistent optional copy versus executed required-document validation. S23 follows the executed validator; native copy/validation alignment requires a separate implementation decision.','- Password change logs out on success. Email change verifies both old and new addresses with the shared OTP challenge.','- Privacy preferences and device permissions are separate. Notification capabilities and menu visibility come from the server/workspace.','- ProfileScreen and RegisterFlowScreen are dispatch/flow hosts; they do not inflate the new-screen count. Tenant and owner profiles remain distinct.','','## Theme and layout contract','','Reuse the original design tokens, Readex Pro headings, IBM Plex Sans Arabic body, real signature, pine actions and restrained arches. System is default, Light/Dark persist and follow OS in System. Switching theme preserves drafts, scroll and review state. Native ThemeCubit, storage key, 320ms/easeInOutCubic and reduced-motion policy remain implementation constraints. The prototype reuses the original compact type scale and component proportions; native large text and safe areas still require implementation checks.','','## Per-screen contract','']
for s in screens:
    audit += [f"<a id=\"{s['id'].lower()}\"></a>\n\n### {s['id']} — {s['english']}",'',f"Source: `{s['source']}`",'', 'Original visual references: '+', '.join(s['visualReference'])+'.','',s['behavior'],'', 'Required states: '+', '.join(s['requiredStates'])+'.','', 'Read dependencies: '+', '.join('`'+d['source']+'`' for d in s['dependencies'])+'.','']
audit += ['## Review boundary','','Mockup state selectors expose loading, read failure, empty and specific workflow variants. These are local design demonstrations; pending writes must keep real loaded content and drafts in Flutter. Unrepresented destinations explain the next app step. Production navigation, APIs, entitlement checks and confirmations remain authoritative. Sprint 2 is not started.']
(OUT/'AUDIT.md').write_text('\n'.join(audit)+'\n')

state_names={'default':'الأساسية','loading':'تحميل','server-error':'خطأ بالخادم','empty':'فارغة','pending':'قيد المراجعة','approved':'مقبولة','rejected':'مرفوضة','incomplete':'غير مكتملة','unknown':'غير معروفة','verify-old':'تأكيد الحالي','enter-new':'البريد الجديد','verify-new':'تأكيد الجديد','expired':'منتهية','complete':'مكتملة'}
# Every rendered optional state is separately labeled; required implementation states are recorded in the manifest.
for s in screens:
    if 'loading' in s['requiredStates']:
        s['variants']['loading']='<div aria-label="جار التحميل" class="loading-sample">'+''.join('<div class="skeleton"></div>' for _ in range(7))+'<p>جار تحميل البيانات…</p></div>'
    if 'server-error' in s['requiredStates']:
        s['variants']['server-error']=((note('تعذّر حفظ التغييرات. بياناتك ما زالت موجودة؛ حاول مرة أخرى.','error','help')+s['content']) if s['id'] in ['S21','S22','S23','S27','S30','S31','S32','S35','S39'] else intro('تعذّر إكمال الخطوة.','رسالة خطأ توضيحية. راجع الاتصال وحاول من جديد.','help')+button('إعادة المحاولة',action='reset-state',kind='primary wide'))
    if 'empty' in s['requiredStates'] and s['id'] in ['S26','S30','S33','S36','S37','S39','S40']:
        s['variants']['empty']=intro('لا توجد بيانات لعرضها.','ستظهر التحديثات المتاحة لحسابك هنا.','file')+button('تحديث',action='reset-state',kind='secondary wide')

payload={s['id']:{k:s[k] for k in ['content','footer','variants']} for s in screens}
# JSON in a script tag: escape markup terminators while preserving original strings.
payload_json=json.dumps(payload,ensure_ascii=False).replace('</','<\\/')
articles=[]
for s in screens:
    opts='<option value="default">الأساسية</option>'+''.join(f'<option value="{v}">{state_names.get(v,v)}</option>' for v in s['variants'])
    path='../../../../../../'+s['source']
    articles.append(f'''<article class="screen sprint-screen" id="{s['id']}" data-group="{s['group']}"><div class="screen-head"><h2><span>{s['id']}</span> {s['name']}</h2><button data-focus="{s['id']}" aria-label="تكبير {s['name']}">تكبير ↗</button></div><label class="state-control">حالة المعاينة <select data-state="{s['id']}">{opts}</select></label><div class="phone layout-{s['layout']}" data-screen="{s['id']}">{status_chrome.replace('class="status"','class="status dark"') if s['layout']=='hub' else status_chrome}{s['header']}<main class="phone-scroll">{s['content']}</main><div class="phone-footer">{s['footer']}</div><div class="home-indicator"></div></div><p class="screen-note">{e(s['english'])} · <a href="AUDIT.md#{s['id'].lower()}">ملاحظات السلوك</a></p><a class="screen-source" href="{path}">{e(s['source'].split('/features/')[-1])}</a></article>''')
controls='<div class="segmented" aria-label="المظهر">'+''.join(f'<button data-mode="{m}">{t}</button>' for m,t in [('light','فاتح'),('dark','داكن'),('system','حسب الجهاز')])+'</div>'
body=f'''<div class="atlas"><header class="atlas-intro"><div><h1>هوية واحدة. والرحلة بتكمل.</h1><p>٢٠ شاشة جديدة على نسق المقترح الأصلي · الحساب والهوية، الأمان، الإشعارات والمساعدة.</p><p class="sheet-label">S21–S40 · مقترح للمراجعة · بيانات وتفاعلات محلية توضيحية</p></div>{logo}</header><div class="toolbar">{controls}<label>المجموعة <select id="group-filter"><option value="all">كل الشاشات · ٢٠</option><option value="account">التسجيل والهوية</option><option value="profile">الملف والإعدادات</option><option value="security">الأمان</option><option value="notifications">الإشعارات</option><option value="support">المساعدة</option></select></label><a href="../../design-map.html">خريطة التصميم ↗</a><a href="../../index.html">المقترح الأصلي · S01–S20</a><a href="../SPRINT-PLAN.md">خطة السبرنتات</a></div><div class="review-gate"><b>سبرنت ١ · جاهز للمراجعة</b><span>السبرنت التالي يبدأ بعد تأكيدك. لم تتغير شاشات Flutter.</span></div><div class="gallery">{''.join(articles)}</div><footer class="atlas-footer"><a href="AUDIT.md">تدقيق السلوك والمصادر</a><a href="screen-manifest.json">بيانات الشاشات</a><span>النماذج للعرض فقط · لا تُرسل بيانات أو مستندات.</span></footer></div><div class="toast" role="status" hidden></div><dialog class="focus-dialog"><div class="focus-controls"><button data-prev>السابق</button><b data-focus-title></b><button data-next>التالي</button><button data-close>إغلاق</button></div><div class="focus-body"></div></dialog><dialog class="confirm-dialog"><h3 data-confirm-title></h3><p data-confirm-copy></p><div class="confirm-actions"><button class="primary" data-confirm>تأكيد المعاينة</button><button class="secondary" data-cancel>إلغاء</button></div></dialog>'''
css=(HERE/'sprint.css').read_text()
js=(HERE/'sprint.js').read_text()
html=f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>سكون · Sprint 1 · S21–S40</title><style>{shared_style}\n{css}</style></head><body>{body}<script type="application/json" id="screen-data">{payload_json}</script><script>{js}</script></body></html>'''
(OUT/'index.html').write_text(html)
print(json.dumps(inventory['counts']))
print('Built Sprint 1 only: '+str(OUT/'index.html'))

# Refresh the main page after any completed batch is rebuilt.
import runpy
runpy.run_path(str(BASE/'build_gallery.py'),run_name='__main__')
