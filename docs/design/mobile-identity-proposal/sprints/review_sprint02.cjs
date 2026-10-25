/* npm install --prefix /tmp/sukoon-design-review playwright; PLAYWRIGHT_MODULE=... node review_sprint.cjs */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/sukoon-design-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const base=path.join(__dirname,'sprint-02'),out=path.join(base,'exports');fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(base,'screen-manifest.json')));
const report={contrast:{},screens:manifest.length,themes:[],widths:[],variants:[],interactions:[],errors:[],externalRequests:[],limitations:['Browser prototype only; no Flutter/device/API tests.','Maps are schematic offline illustrations; gallery and launch have fixed source-defined surfaces.','Later sprints have source inventory only; behavioral audit happens within each sprint.']};
(async()=>{
 const launch=process.env.CHROME_EXECUTABLE?{executablePath:process.env.CHROME_EXECUTABLE}:{executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'};
 const browser=await chromium.launch({...launch,headless:true});
 const context=await browser.newContext({viewport:{width:1680,height:1200},deviceScaleFactor:2,reducedMotion:'reduce',colorScheme:'light'});
 const p=await context.newPage();p.on('pageerror',err=>report.errors.push(err.message));p.on('request',r=>{if(/^https?:/.test(r.url()))report.externalRequests.push(r.url())});

 const tokens=JSON.parse(fs.readFileSync(path.join(__dirname,'../design-tokens.json')));
 function lum(hex){return hex.match(/[a-f0-9]{2}/gi).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0)}
 for(const theme of ['light','dark']){report.contrast[theme]={};for(const [fg,bg] of [['text','canvas'],['text','surface'],['muted','canvas'],['muted','surface'],['accent','chip'],['on-action','action'],['success','success-bg'],['warning','warning-bg'],['error','error-bg'],['info','info-bg']]){const a=lum(tokens[fg][theme]),b=lum(tokens[bg][theme]),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);assert(ratio>=4.5);report.contrast[theme][fg+'/'+bg]=+ratio.toFixed(2)}}
 const url=pathToFileURL(path.join(base,'index.html')).href;
 const load=async(theme='light')=>{await p.goto(url+'?theme='+theme);await p.evaluate(()=>document.fonts.ready)};
 const noOverflow=async()=>p.locator('.phone').evaluateAll(es=>es.filter(el=>{const m=el.querySelector('main');return el.scrollWidth>el.clientWidth+1||m.scrollWidth>m.clientWidth+1}).map(el=>el.dataset.screen));
 for(const s of manifest){assert(fs.existsSync(path.resolve(__dirname,'../../../../..',s.source)),s.source)}
 await load();assert.equal(await p.locator('.screen').count(),20);assert.equal(await p.locator('.phone').count(),20);
 // Compare shared visual primitives to the original atlas in the same browser.
 const reference=await context.newPage();await reference.goto(pathToFileURL(path.join(__dirname,'../original-twenty.html')).href+'?theme=light');await reference.evaluate(()=>document.fonts.ready);
 report.originalStyleParity=[];
 const contracts=[
  ['input','.field input',['fontFamily','fontSize','fontWeight','minHeight','borderRadius','backgroundColor']],
  ['primary action','.primary',['fontFamily','fontSize','fontWeight','minHeight','borderRadius','backgroundColor','color']],
  ['wordmark','.auth-mark',['width','height','color']],
  ['phone frame','.phone',['width','height','borderRadius','borderTopWidth','backgroundColor']],
  ['top bar','.topbar h2',['fontFamily','fontSize','fontWeight']],
  ['OS chrome','.status',['fontFamily','fontSize','height']],
 ];
 for(const [name,selector,properties] of contracts){
   const originalSelector=selector==='.phone'?'#S02 .phone':'#S02 '+selector;
   const revisedSelector=selector==='.auth-mark'?'#S53 .auth-mark':selector==='.phone'?'#S44 .phone':'#S44 '+selector;
   const values=async(page,query)=>page.locator(query).first().evaluate((el,keys)=>Object.fromEntries(keys.map(k=>[k,getComputedStyle(el)[k]])),properties);
   const original=await values(reference,originalSelector),revised=await values(p,revisedSelector);assert.deepEqual(revised,original,name+' original style parity');report.originalStyleParity.push({component:name,result:'matches original',properties:revised});
 }
 await reference.close();

 for(const theme of ['light','dark']){
  await load(theme);assert.equal(await p.locator('html').getAttribute('data-theme'),theme);assert.deepEqual(await noOverflow(),[]);
  await p.evaluate(()=>document.body.classList.add('export'));
  await p.evaluate(()=>window.scrollTo({top:0,left:0,behavior:'instant'}));
  await p.screenshot({path:path.join(out,theme+'-overview.png'),fullPage:true,scale:'css'});
  for(const s of manifest){
   const phone=p.locator('#'+s.id+' .phone');
   await phone.evaluate(el=>{el.style.cssText='position:fixed;top:0;left:0;margin:0;z-index:1000;width:360px;height:800px';window.scrollTo(0,0)});
   await p.screenshot({path:path.join(out,s.id+'-'+theme+'.png'),clip:{x:0,y:0,width:360,height:800}});
   await phone.evaluate(el=>el.removeAttribute('style'));
  }
  for(let i=0;i<5;i++){
   await load(theme);await p.evaluate(()=>document.body.classList.add('export'));
   await p.locator('.screen').evaluateAll((es,offset)=>es.forEach((el,n)=>el.hidden=n<offset||n>=offset+4),i*4);
   await p.evaluate(()=>window.scrollTo({top:0,left:0,behavior:'instant'}));
   await p.screenshot({path:path.join(out,theme+'-sheet-'+(i+1)+'.png'),fullPage:true,scale:'css'});
  }
  report.themes.push({theme,screens:20,individualSize:[720,1600],horizontalOverflow:[]});
 }
 await load();
 for(const w of [360,390,768,1680]){await p.setViewportSize({width:w,height:1000});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'page '+w);assert.deepEqual(await noOverflow(),[]);report.widths.push({width:w,overflow:false})}
 await p.setViewportSize({width:1680,height:1200});
 // Every rendered variant in both modes.
 for(const theme of ['light','dark']){
  await load(theme);
  const options=await p.locator('[data-state]').evaluateAll(es=>es.map(el=>({id:el.dataset.state,states:[...el.options].map(x=>x.value)})));
  for(const item of options){for(const state of item.states){await p.locator(`[data-state="${item.id}"]`).selectOption(state);assert.deepEqual(await noOverflow(),[],item.id+' '+state);report.variants.push({theme,id:item.id,state})}await p.locator(`[data-state="${item.id}"]`).selectOption('default')}
 }
 await load();
 await p.locator('#S44 [name=subject]').fill('مشكلة في عرض الصور');await p.locator('#S44 [name=description]').fill('تفاصيل توضيحية محفوظة أثناء مراجعة النموذج.');await p.locator('#S44 main').evaluate(el=>el.scrollTop=90);const scroll=await p.locator('#S44 main').evaluate(el=>el.scrollTop);
 await p.locator('[data-mode=dark]').click();assert.equal(await p.locator('#S44 [name=subject]').inputValue(),'مشكلة في عرض الصور');assert.equal(await p.locator('#S44 main').evaluate(el=>el.scrollTop),scroll);
 await p.goto(url);assert.equal(await p.locator('html').getAttribute('data-theme'),'dark');await p.locator('[data-mode=system]').click();await p.emulateMedia({colorScheme:'dark'});await p.waitForFunction(()=>document.documentElement.dataset.theme==='dark');await p.emulateMedia({colorScheme:'light'});await p.waitForFunction(()=>document.documentElement.dataset.theme==='light');report.interactions.push('Theme persistence/live System and draft/scroll preservation');
 await p.locator('#group-filter').selectOption('الدعم');assert.equal(await p.locator('.screen:visible').count(),4);await p.locator('#group-filter').selectOption('all');report.interactions.push('Group filter');
 await p.locator('#S44 [name=subject]').fill('عنوان محفوظ');await p.locator('#S44 [name=description]').fill('نص طويل يظل محفوظًا عند فشل الإرسال.');await p.locator('[data-state=S44]').selectOption('error');assert.equal(await p.locator('#S44 [name=description]').inputValue(),'نص طويل يظل محفوظًا عند فشل الإرسال.');await p.locator('[data-state=S44]').selectOption('default');assert.equal(await p.locator('#S44 [name=subject]').inputValue(),'عنوان محفوظ');report.interactions.push('Form error retains input and multiline draft');
 await p.locator('[data-focus=S44]').click();assert.equal(await p.locator('.focus-body [name=subject]').inputValue(),'عنوان محفوظ');await p.locator('.focus-body [name=subject]').fill('تعديل في العرض المكبر');await p.locator('[data-close]').click();assert.equal(await p.locator('#S44 [name=subject]').inputValue(),'تعديل في العرض المكبر');report.interactions.push('Focused preview preserves original controls');
 await p.locator('#S44 [data-action=support-topic][data-value=payment]').click();assert.equal(await p.locator('#S44 [data-payment-context]').isVisible(),true);await p.locator('#S44 [data-action=ticket-attachment]').click();assert.equal(await p.locator('#S44 .sample-file').count(),1);await p.locator('#S44 [data-action=remove-ticket-attachment]').click();assert.equal(await p.locator('#S44 .sample-file').count(),0);report.interactions.push('Payment topic conditional fields and local attachment add/remove');
 await p.locator('#S44 button[form=ticket-form]').click();assert.equal(await p.locator('.confirm-dialog').evaluate(el=>el.open),true);await p.locator('[data-cancel]').click();await p.locator('[data-state=S44]').selectOption('unknown-outcome');assert.equal(await p.locator('#S44 [name=subject]').isDisabled(),true);assert.equal(await p.locator('#S44 button[form=ticket-form]').count(),0);assert.equal(await p.locator('#S44 [data-action=recover-ticket]').isVisible(),true);report.interactions.push('Ticket submission confirmation and uncertain-write recovery gate');
 await p.locator('#S45 [name=reply]').fill('<script>local text</script>');await p.locator('#S45 button[type=submit]').click();assert.equal(await p.locator('#S45 .support-messages .bubble').count(),3);assert.equal(await p.locator('#S45 .support-messages script').count(),0);await p.locator('[data-state=S45]').selectOption('resolved');assert.equal(await p.locator('#S45 [name=reply]').isDisabled(),true);assert.equal(await p.locator('#S45 button[type=submit]').isDisabled(),true);report.interactions.push('Local reply escapes text and resolved tickets block new replies');
 await p.locator('#S43 [data-action=attachment-zoom]').click();assert.equal(await p.locator('#S43 [data-attachment-image]').getAttribute('data-zoom'),'true');await p.locator('[data-state=S43]').selectOption('session-ended');assert.equal(await p.locator('#S43 img').count(),0);report.interactions.push('Attachment zoom and session-ended preview removal');
 await p.locator('[data-state=S47]').selectOption('privacy');assert((await p.locator('#S47 main').textContent()).includes('سياسة الخصوصية'));await p.locator('[data-state=S47]').selectOption('about');assert.equal(await p.locator('#S47 .auth-mark').count(),1);await p.locator('[data-state=S48]').selectOption('accepted');assert((await p.locator('#S48 main').textContent()).includes('النسخة السابقة غير متاحة'));assert.equal(await p.locator('#S48 .policy-description').count(),0);report.interactions.push('Public-page variants and missing historical policy does not fall back to current');
 await p.locator('#S49 [data-switch=automatic]').click();assert.equal(await p.locator('#S49 [data-switch=automatic]').getAttribute('aria-checked'),'false');await p.locator('#S49 [data-action=guide-home]').click();assert.equal(await p.locator('.confirm-dialog').evaluate(el=>el.open),true);await p.locator('[data-cancel]').click();await p.locator('#S50 [data-value=older]').click();assert.equal(await p.locator('[data-state=S50]').inputValue(),'older-version');report.interactions.push('Guide preference/replay confirmation and release-version selection');
 await p.locator('#S51 [data-action=recover-ticket]').click();assert((await p.locator('.toast').textContent()).includes('دون إعادة إرسال'));await p.locator('[data-state=S52]').selectOption('startup-error');await p.locator('#S52 [data-action=retry-startup]').click();assert.equal(await p.locator('#S52 .launch-art').count(),1);for(const mode of ['dark','light']){await p.locator(`[data-mode=${mode}]`).click();assert.equal(await p.locator('#S52').locator('.phone').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(246, 242, 233)');assert.equal(await p.locator('#S55').locator('.phone').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(16, 23, 19)')}report.interactions.push('Operation recovery does not resend; startup retry and fixed launch/media surfaces');
 await p.locator('#S53 [data-action=workspace][data-value=company]').click();assert((await p.locator('.toast').textContent()).includes('لا يمنح صلاحيات'));report.interactions.push('Workspace preview does not grant company authority');
 await p.locator('#S54 [data-marker="1"]').click();assert.equal(await p.locator('#S54 [data-map-selection] h3').textContent(),'استوديو مفروش');await p.locator('#S54 [data-action=map-area]').click();assert((await p.locator('.toast').textContent()).includes('المحمّلة فقط'));report.interactions.push('Map marker/detail selection and loaded-only viewport scope');
 await p.locator('#S55 [data-action=photo-next]').click();assert.equal(await p.locator('#S55 [data-action=photo-next]').isDisabled(),true);assert.equal(await p.locator('#S55 [data-photo-name]').textContent(),'الغرفة الثانية');await p.locator('#S55 [data-action=photo-prev]').click();assert.equal(await p.locator('#S55 [data-action=photo-prev]').isDisabled(),true);report.interactions.push('Photo viewer previous/next bounds and thumbnail synchronization');
 await p.locator('#S56 [data-action=recent-search]').first().click();assert.equal(await p.locator('#S56 [name=query]').inputValue(),'المعادي');report.interactions.push('Recent search populates search draft');
 await p.locator('#S57 [data-action=cancel-visit]').click();await p.locator('[data-cancel]').click();assert.equal(await p.locator('#S57 [data-action=cancel-visit]').count(),1);await p.locator('#S57 [data-action=cancel-visit]').click();await p.locator('[data-confirm]').click();assert.equal(await p.locator('[data-state=S57]').inputValue(),'cancelled');await p.locator('[data-state=S57]').selectOption('stale');assert.equal(await p.locator('#S57 [data-action=cancel-visit]').count(),0);report.interactions.push('Viewing cancellation confirmation and stale-data mutation gate');
 await p.locator('#S58 [data-action=owner-tab][data-value=groups]').click();assert((await p.locator('#S58 [data-owner-panel]').textContent()).includes('المجموعات'));await p.locator('[data-state=S58]').selectOption('restricted');assert.equal(await p.locator('#S58 .tabs button').count(),1);report.interactions.push('Owner capability-gated request tabs');
 await p.locator('[data-state=S59]').selectOption('no-location');assert.equal(await p.locator('#S59 [data-action=confirm-location]').isDisabled(),true);await p.locator('#S59 [data-pick-map]').press('Enter');assert.equal(await p.locator('#S59 [data-action=confirm-location]').isEnabled(),true);await p.locator('[data-state=S59]').selectOption('default');await p.locator('#S59 [data-action=satellite-demo]').click();assert.equal(await p.locator('#S59 .map-stage').getAttribute('class'),'map-stage picker-map satellite');report.interactions.push('Location confirm gates, keyboard selection and local satellite view');
 await p.locator('#S60 [data-action=remove-property-photo]').first().click();assert.equal(await p.locator('#S60 .editor-photo').count(),9);assert.equal(await p.locator('#S60 [data-action=media-next]').isDisabled(),true);await p.locator('#S60 [data-action=add-property-photo]').click();assert.equal(await p.locator('#S60 [data-action=media-next]').isEnabled(),true);await p.locator('#S60 [data-action=remove-property-video]').click();assert.equal(await p.locator('#S60 [data-action=media-next]').isDisabled(),true);await p.locator('#S60 [data-action=add-property-video]').click();assert.equal(await p.locator('#S60 [data-action=media-next]').isEnabled(),true);await p.locator('#S60 [data-action=main-property-photo]').nth(2).click();assert.equal(await p.locator('#S60 .main-photo[aria-pressed=true]').count(),1);report.interactions.push('Media minimum photo count, required video and single main photo');
 // Cross-sprint navigation carries appearance and opens the intended screen.
 await p.locator('#S41 [data-go=S27]').click();await p.waitForURL(/sprint-01\/index.html.*#S27/);assert((await p.locator('.focus-dialog').evaluate(el=>el.open))===true);report.interactions.push('Cross-sprint source-linked navigation preserves theme');
 assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);
 report.result='pass';fs.writeFileSync(path.join(base,'review-results.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({result:report.result,screens:report.screens,variantChecks:report.variants.length,interactions:report.interactions.length,errors:report.errors,externalRequests:report.externalRequests}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
