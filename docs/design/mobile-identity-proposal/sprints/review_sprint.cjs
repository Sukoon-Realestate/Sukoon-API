/* npm install --prefix /tmp/sukoon-design-review playwright; PLAYWRIGHT_MODULE=... node review_sprint.cjs */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/sukoon-design-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const base=path.join(__dirname,'sprint-01'),out=path.join(base,'exports');fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(base,'screen-manifest.json')));
const report={contrast:{},screens:manifest.length,themes:[],widths:[],variants:[],interactions:[],errors:[],externalRequests:[],limitations:['Browser prototype only; no Flutter/device/API tests.','English selection demonstrates selection, not a full English mockup.','Later sprints have source inventory only; behavioral audit happens within each sprint.']};
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
   const revisedSelector=selector==='.phone'?'#S22 .phone':'#S22 '+selector;
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
 await p.locator('#S21 [name=first]').fill('أحمد');await p.locator('#S21 main').evaluate(el=>el.scrollTop=140);const before=await p.locator('#S21 main').evaluate(el=>el.scrollTop);
 await p.locator('[data-mode=dark]').click();assert.equal(await p.locator('#S21 [name=first]').inputValue(),'أحمد');assert.equal(await p.locator('#S21 main').evaluate(el=>el.scrollTop),before);
 await p.goto(url);assert.equal(await p.locator('html').getAttribute('data-theme'),'dark');
 await p.locator('[data-mode=system]').click();await p.emulateMedia({colorScheme:'dark'});await p.waitForFunction(()=>document.documentElement.dataset.theme==='dark');assert.equal(await p.locator('html').getAttribute('data-theme'),'dark');await p.emulateMedia({colorScheme:'light'});await p.waitForFunction(()=>document.documentElement.dataset.theme==='light');assert.equal(await p.locator('html').getAttribute('data-theme'),'light');report.interactions.push('Theme persistence, live System changes, draft/scroll preservation');
 await p.locator('#group-filter').selectOption('security');assert.equal(await p.locator('.screen:visible').count(),5);await p.locator('#group-filter').selectOption('all');report.interactions.push('Group filter');
 await p.locator('#S27 [name=name]').fill('اسم معدل');await p.locator('[data-state=S27]').selectOption('server-error');assert.equal(await p.locator('#S27 [name=name]').inputValue(),'اسم معدل');await p.locator('[data-state=S27]').selectOption('default');assert.equal(await p.locator('#S27 [name=name]').inputValue(),'اسم معدل');report.interactions.push('Failed-save variant retains form draft');
 await p.locator('[data-focus=S27]').click();assert.equal(await p.locator('.focus-body [name=name]').inputValue(),'اسم معدل');await p.locator('.focus-body [name=name]').fill('داخل المعاينة');await p.locator('[data-close]').click();assert.equal(await p.locator('#S27 [name=name]').inputValue(),'داخل المعاينة');report.interactions.push('Focused preview moves original screen and preserves form');
 await p.locator('#S22 [name=email]').fill('review@example.com');await p.locator('#S22 button[type=submit]').click();assert(await p.locator('#S22 main').textContent().then(t=>t.includes('re****@example.com')));await p.locator('#S22 [data-action=reset-state]').click();assert.equal(await p.locator('#S22 [name=email]').count(),1);report.interactions.push('Password recovery sent state and change-email return');
 const register=p.locator('#S21');await register.locator('[name=first]').fill('أحمد');await register.locator('[name=last]').fill('محمود');await register.locator('[name=phone]').fill('01012345678');await register.locator('[name=email]').fill('review@example.com');await register.locator('[name=password]').fill('abcdefgh');await register.locator('[name=confirm]').fill('wrongpassword');await register.locator('button[type=submit]').click();assert.equal(await p.locator('.confirm-dialog').evaluate(el=>el.open),false);await register.locator('[name=confirm]').fill('abcdefgh');await register.locator('button[type=submit]').click();assert.equal(await p.locator('.confirm-dialog').evaluate(el=>el.open),true);await p.locator('[data-cancel]').click();report.interactions.push('Registration validation, mismatch recovery, current eight-character policy');
 await p.locator('#S23 [data-action=submit-kyc]').click();assert.notEqual(await p.locator('#S23 .inline-feedback').textContent(),'');report.interactions.push('KYC incomplete submission blocked');
 await p.locator('#S35 [name=ack]').check();assert.equal(await p.locator('#S35 [data-action=delete-account]').isEnabled(),true);await p.locator('#S35 [data-action=delete-account]').click();assert.equal(await p.locator('.confirm-dialog').evaluate(el=>el.open),true);await p.locator('[data-cancel]').click();report.interactions.push('Account deletion acknowledgement and confirmation');
 await p.locator('#S33 [data-action=revoke-session]').click();await p.locator('[data-confirm]').click();assert.equal(await p.locator('#S33 .session-card').count(),1);report.interactions.push('Confirmed local revoke of other session');
 await p.locator('#S32 [data-action=email-start]').click();assert.equal(await p.locator('#S32 .otp-row input').count(),6);for(let i=0;i<6;i++)await p.locator('#S32 .otp-row input').nth(i).fill(String(i+1));await p.locator('#S32 button[type=submit]').click();await p.locator('#S32 [name=email]').fill('new@example.com');await p.locator('#S32 button[type=submit]').click();for(let i=0;i<6;i++)await p.locator('#S32 .otp-row input').nth(i).fill(String(i+1));await p.locator('#S32 button[type=submit]').click();assert.equal(await p.locator('[data-state=S32]').inputValue(),'complete');report.interactions.push('Email old OTP → new email → new OTP → completion');
 await p.locator('#S30 [data-switch=location]').click();assert.equal(await p.locator('#S30 [data-switch=location]').getAttribute('aria-checked'),'true');assert.equal(await p.locator('#S39 [data-switch=security]').isDisabled(),true);report.interactions.push('Privacy switch and server-locked notification example');
 await p.locator('#S37 [data-action=read-all]').click();assert.equal(await p.locator('#S37 .unread-dot').count(),0);report.interactions.push('Mark all read');
 await p.locator('#S40 [data-faq-search]').fill('غيرموجود');assert.equal(await p.locator('#S40 [data-faq-empty]').isVisible(),true);await p.locator('#S40 [data-faq-search]').fill('');await p.locator('#S40 details').first().locator('summary').click();assert.equal(await p.locator('#S40 details').first().getAttribute('open'),'');report.interactions.push('FAQ search, empty results and expansion');
 // The prototype remains fully local.
 assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);
 report.result='pass';fs.writeFileSync(path.join(base,'review-results.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({result:report.result,screens:report.screens,variantChecks:report.variants.length,interactions:report.interactions.length,errors:report.errors,externalRequests:report.externalRequests}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
