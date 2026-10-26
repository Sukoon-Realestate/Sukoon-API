const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/sukoon-design-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');const {pathToFileURL}=require('url');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1680,height:1200},deviceScaleFactor:2,reducedMotion:'reduce',colorScheme:'light'});
 await context.addInitScript(()=>history.scrollRestoration="manual");const page=await context.newPage();let errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
 const noOverflow=()=>page.locator('.phone').evaluateAll(es=>es.filter(e=>e.scrollWidth>e.clientWidth+1||e.querySelector('main').scrollWidth>e.querySelector('main').clientWidth+1).map(e=>e.dataset.screen));
 const combined={sprints:[],screens:75,result:'pending'};
 for(let n=11;n<=14;n++){
  errors=[];requests=[];const dir=path.join(__dirname,'sprint-'+String(n).padStart(2,'0')),out=path.join(dir,'exports');fs.mkdirSync(out,{recursive:true});
  const manifest=JSON.parse(fs.readFileSync(path.join(dir,'screen-manifest.json')));assert.equal(manifest.length,(n===14?15:20));
  const url=pathToFileURL(path.join(dir,'index.html')).href;const load=async(theme='light')=>{await page.goto(url+'?theme='+theme);await page.evaluate(()=>document.fonts.ready);await page.addStyleTag({content:'html{scroll-behavior:auto!important;overflow-anchor:none}body{overflow-anchor:none}'})};
  const report={sprint:n,screens:manifest.length,sourceHashes:[],nativeSubpageExports:[],themes:[],widths:[],variants:[],interactions:[],errors,externalRequests:requests,limitations:['Browser mockups only; no native device/API/provider tests.','Financial, signature, publication, evidence and AI outcomes are illustrative.']};
  for(const s of manifest){const src=path.resolve(__dirname,'../../../../..',s.source);assert(fs.existsSync(src));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(src)).digest('hex'),s.sha256,s.source);report.sourceHashes.push(s.id)}
  for(const theme of ['light','dark']){
   await load(theme);assert.equal(await page.locator('.screen').count(),manifest.length);assert.deepEqual(await noOverflow(),[]);
   if(process.env.SKIP_EXPORT!=='1'){
   await page.evaluate(()=>document.body.classList.add('export'));await page.screenshot({path:path.join(out,theme+'-overview.png'),fullPage:true,scale:'css'});
   for(const s of manifest){const phone=page.locator('#'+s.id+' .phone');await phone.evaluate(el=>{el.style.cssText='position:fixed;top:0;left:0;margin:0;z-index:1000;width:360px;height:800px';window.scrollTo(0,0)});await page.screenshot({path:path.join(out,s.id+'-'+theme+'.png'),clip:{x:0,y:0,width:360,height:800}});await phone.evaluate(el=>el.removeAttribute('style'));const bytes=fs.readFileSync(path.join(out,s.id+'-'+theme+'.png'));assert.equal(bytes.readUInt32BE(16),720);assert.equal(bytes.readUInt32BE(20),1600)}
   const sheetPage=await browser.newPage({viewport:{width:1680,height:1200},deviceScaleFactor:1,reducedMotion:'reduce'});
   sheetPage.on('pageerror',e=>errors.push(e.message));sheetPage.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
   await sheetPage.addInitScript(()=>history.scrollRestoration='manual');
   for(let sheet=0;sheet<Math.ceil(manifest.length/4);sheet++){
    await sheetPage.goto(url+'?theme='+theme);await sheetPage.evaluate(()=>document.fonts.ready);
    await sheetPage.addStyleTag({content:'html{scroll-behavior:auto!important;overflow-anchor:none}body{overflow-anchor:none}'});
    await sheetPage.evaluate(start=>{document.body.classList.add('export');[...document.querySelectorAll('.screen')].forEach((el,i)=>el.hidden=i<start||i>=start+4)},sheet*4);
    await sheetPage.evaluate(async()=>{window.scrollTo(0,0);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))});
    assert.equal(await sheetPage.evaluate(()=>scrollY),0);
    assert.equal(await sheetPage.locator('.screen:visible').count(),Math.min(4,manifest.length-sheet*4));
    await sheetPage.screenshot({path:path.join(out,theme+'-sheet-'+(sheet+1)+'.png'),fullPage:true,scale:'css'});
   }
   await sheetPage.close();
   }
   report.themes.push({theme,individuals:manifest.length,size:[720,1600]});
   await load(theme);
   for(const s of manifest){const select=page.locator(`[data-state="${s.id}"]`);const options=await select.locator('option').evaluateAll(es=>es.map(e=>e.value));for(const state of options){await select.selectOption(state);assert.deepEqual(await noOverflow(),[],s.id+' '+state);if(['unknown-outcome','saving'].includes(state)&&await page.locator('#'+s.id+' fieldset').count()){assert.equal(await page.locator('#'+s.id+' fieldset').first().evaluate(el=>el.disabled),true)}if(['stale','restricted','read-only','legacy-read-only'].includes(state)){assert.equal(await page.locator('#'+s.id+' form[data-form=batch-form]').count(),0)}if(process.env.SKIP_EXPORT!=='1'&&state!=='default'&&Object.values(s.coveredNativeClasses).includes(state)){
     const nativeClass=Object.entries(s.coveredNativeClasses).find(([name,value])=>value===state)[0];const nativeDir=path.join(out,'native-subpages');fs.mkdirSync(nativeDir,{recursive:true});
     await page.locator('#'+s.id+' main').evaluate(el=>el.scrollTop=0);
     const target=path.join(nativeDir,nativeClass+'-'+theme+'.png');const nativePhone=page.locator('#'+s.id+' .phone');await nativePhone.evaluate(el=>{el.style.cssText='position:fixed;top:0;left:0;margin:0;z-index:1000;width:360px;height:800px';window.scrollTo(0,0)});await page.screenshot({path:target,clip:{x:0,y:0,width:360,height:800}});await nativePhone.evaluate(el=>el.removeAttribute('style'));
     const bytes=fs.readFileSync(target);assert.equal(bytes.readUInt32BE(16),720);assert.equal(bytes.readUInt32BE(20),1600);
     report.nativeSubpageExports.push({id:s.id,nativeClass,state,theme});
    }
    report.variants.push({id:s.id,theme,state})}await select.selectOption('default')}
  }
  await load();
  for(const width of [360,390,768,1680]){await page.setViewportSize({width,height:1100});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(await noOverflow(),[]);report.widths.push({width,overflow:false})}await page.setViewportSize({width:1680,height:1200});
  const forms=await page.locator('.phone form[data-form=batch-form]').evaluateAll(es=>es.map(e=>e.closest('.phone').dataset.screen));assert(forms.length>0);
  const chosen=forms.find(id=>manifest.find(s=>s.id===id).renderedVariants.includes('error'));
  const editor=page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first();
  if(await editor.count()){
   await editor.fill('مسودة مراجعة محلية');const value=await editor.inputValue();await page.locator(`[data-state="${chosen}"]`).selectOption('error');assert.equal(await page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first().inputValue(),value);await page.locator(`[data-state="${chosen}"]`).selectOption('default');assert.equal(await page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first().inputValue(),value);report.interactions.push('Multiline/input draft survives error and return');
   await page.locator('[data-mode=dark]').click();assert.equal(await editor.inputValue(),value);report.interactions.push('Theme change preserves form');
  }
  await page.locator('[data-mode=system]').click();await page.emulateMedia({colorScheme:'dark'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');await page.emulateMedia({colorScheme:'light'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');report.interactions.push('Live System theme');
  const form=page.locator('#'+chosen+' form[data-form=batch-form]').first();await form.locator('input[required],textarea[required]').evaluateAll(es=>es.forEach(el=>{if(!el.value)el.value=el.type==='number'?'2':el.type==='date'?'2026-11-01':el.type==='time'?'10:00':'بيانات توضيحية للمراجعة'}));for(const el of await form.locator('[data-batch-ack]').all())await el.check();
  await form.locator('button[type=submit]').click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),true);await page.locator('[data-cancel]').click();assert.equal(await form.locator('.batch-form-feedback').count(),0);
  await form.locator('button[type=submit]').click();await page.locator('[data-confirm]').click();assert.equal(await form.locator('.batch-form-feedback').count(),1);assert((await form.locator('.batch-form-feedback').textContent()).includes('محليًا'));report.interactions.push('Review confirmation, cancel and local-only result');
  await page.locator(`[data-state="${chosen}"]`).selectOption('unknown-outcome');assert.equal(await page.locator('#'+chosen+' [data-action=batch-recover]').count(),1);await page.locator('#'+chosen+' [data-action=batch-recover]').click();assert((await page.locator('.toast').textContent()).includes('لا يتم تكرار'));report.interactions.push('Unknown outcome blocks re-submit and checks original attempt');await page.locator(`[data-state="${chosen}"]`).selectOption('default');
  await page.locator(`[data-focus="${chosen}"]`).click();await page.locator('[data-close]').click();await page.locator('#'+chosen+' .phone').waitFor({state:'attached'});assert.equal(await page.locator('#'+chosen+' .phone').count(),1);report.interactions.push('Focused preview restores original screen');
  const sensitive=page.locator('[data-action=batch-confirm]').first();if(await sensitive.count()){await sensitive.click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),true);await page.locator('[data-cancel]').click();report.interactions.push('Sensitive action has explicit confirmation')}

  const byFile=file=>manifest.find(s=>s.source.endsWith('/'+file)).id;
  for(const screen of manifest){assert(Object.keys(screen.coveredNativeClasses).length>0);for(const state of Object.values(screen.coveredNativeClasses))assert(state==='default'||screen.renderedVariants.includes(state));}
  report.interactions.push('All native screen classes in each source file map to a rendered primary or subpage variant');
  if(n===11){
   const activation=byFile('company_activation_screen.dart');await page.locator('#'+activation+' [data-variant=activation-review]').click();
   assert.equal(await page.locator('#'+activation+' [name=decision]').count(),1);
   await page.locator('[data-state="'+activation+'"]').selectOption('wrong-account');assert.equal(await page.locator('#'+activation+' form').count(),0);
   assert.equal(await page.locator('#'+activation+' [data-go="'+byFile('company_contact_proof_screen.dart')+'"]').count(),1);
   report.interactions.push('Activation preview and wrong-account proof path remain distinct and gated');
   const publication=page.locator('#'+byFile('student_publication_screen.dart'));
   await publication.locator('[type=submit]').click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),false);
   await publication.locator('[data-batch-ack]').check();await publication.locator('[type=submit]').click();
   assert((await page.locator('.confirm-dialog [data-confirm-copy]').textContent()).includes('البيانات'));await page.locator('[data-cancel]').click();
   report.interactions.push('Student publication requires explicit scoped consent and cancel preserves draft');
   const requests=byFile('company_requests_screen.dart');await page.locator('#'+requests+' [data-variant=request-list]').click();await page.locator('#'+requests+' [data-variant=request-form]').click();
   assert.equal(await page.locator('#'+requests+' form [name=monthlyBudget]').count(),1);report.interactions.push('Request list/detail/wizard destinations render inside one source section');
  }
  if(n===12){
   const csv=page.locator('#'+byFile('company_staff_import_screen.dart'));
   await csv.locator('[name=csv]').fill('name,email,employee_code\n<b>text</b>,one@example.com,DUP\nSecond,two@example.com,DUP');
   await csv.locator('[data-action=final-csv]').click();assert.equal(await csv.locator('.csv-feedback.error').count(),1);
   await csv.locator('[name=csv]').fill('name,email,employee_code\n<b>text</b>,one@example.com,EMP-001');await csv.locator('[data-action=final-csv]').click();
   assert.equal(await csv.locator('.csv-row').count(),1);assert.equal(await csv.locator('.csv-row b').count(),0);assert((await csv.locator('.csv-row').textContent()).includes('<b>text</b>'));
   report.interactions.push('CSV duplicate identities blocked; preview treats cells as text and performs no import');
   const units=page.locator('#'+byFile('unit_batch_screen.dart'));await units.locator('[name=unitCodes]').fill('A-01\nA-01');await units.locator('[data-batch-ack]').check();await units.locator('[type=submit]').click();
   assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),false);assert.equal(await units.locator('[data-final-error]').count(),1);
   await units.locator('[data-variant=unit-batch-result]').click();await units.locator('[data-variant=unit-batch-retry]').click();assert.equal(await units.locator('[name=retryCode]').count(),1);assert.equal(await units.locator('[name=unitCodes]').count(),0);
   report.interactions.push('Unit batch enforces unique codes and retries only the unconfirmed unit');
   const pricing=page.locator('#'+byFile('tender_bid_edit_screen.dart'));assert.equal(await pricing.locator('[data-tier-fields]').isVisible(),false);
   await pricing.locator('[name=pricingRule]').selectOption('1');assert.equal(await pricing.locator('[data-tier-fields]').isVisible(),true);assert.equal(await pricing.locator('[name=rate]').isEnabled(),true);
   await pricing.locator('[name=pricingRule]').selectOption('0');assert.equal(await pricing.locator('[name=rate]').isDisabled(),true);
   report.interactions.push('Tier-specific prices are shown only for the selected pricing rule');
   const bids=byFile('tender_bids_screen.dart');await page.locator('[data-state="'+bids+'"]').selectOption('sealed');assert.equal(await page.locator('#'+bids+' form').count(),0);assert.equal(await page.locator('#'+bids+' .price').count(),0);
   report.interactions.push('Sealed bid state exposes no competing prices or write controls');
  }
  if(n===13){
   const own=page.locator('#'+byFile('tender_consent_screen.dart'));await own.locator('[type=submit]').click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),false);
   await own.locator('[data-batch-ack]').check();await own.locator('[type=submit]').click();assert((await page.locator('.confirm-dialog [data-confirm-copy]').textContent()).includes('تخصك وحدك'));await page.locator('[data-cancel]').click();
   report.interactions.push('Package acceptance requires independent own-allocation consent');
   const needs=page.locator('#'+byFile('living_requirements_screen.dart'));await needs.locator('[data-variant=omitted-inputs]').click();
   assert.equal(await needs.locator('input[type=number]').count(),0);assert((await needs.textContent()).includes('صفرية'));
   await page.locator('[data-state="'+byFile('living_requirements_screen.dart')+'"]').selectOption('living-disclosure');assert.equal(await needs.locator('[name=disclosed]').count(),1);
   report.interactions.push('Omitted private inputs stay absent; disclosure is a separate deliberate step');
   const configure=page.locator('#'+byFile('living_lab_planning_screen.dart'));await configure.locator('[data-variant=living-scenario]').click();assert.equal(await configure.locator('[name=scenarioKind]').count(),1);assert((await configure.textContent()).includes('افتراضي'));
   report.interactions.push('Living scenario is visibly counterfactual and does not alter real membership');
  }
  if(n===14){
   const execution=page.locator('#'+byFile('execution_action_screen.dart'));await page.locator('[data-state="'+byFile('execution_action_screen.dart')+'"]').selectOption('reconcile-step');
   assert.equal(await execution.locator('form').count(),0);assert((await execution.textContent()).includes('دفع جديد'));
   report.interactions.push('Unknown-after-send reconciliation shows no new payment form');
   const detail=byFile('execution_detail_screen.dart');await page.locator('[data-state="'+detail+'"]').selectOption('partial-completion');assert((await page.locator('#'+detail).textContent()).includes('لا يُعاد'));
   report.interactions.push('Partial completion preserves confirmed legs and reviews only the unknown leg');
   const review=page.locator('#'+byFile('scenario_review_screen.dart'));await review.locator('[data-variant=comparison]').click();assert.equal(await review.locator('.comparison-cards .panel').count(),2);
   report.interactions.push('Scenario comparison retains separate labelled plan snapshots');
   const move=byFile('move_execution_screen.dart');await page.locator('[data-state="'+move+'"]').selectOption('expired');assert.equal(await page.locator('#'+move+' form').count(),0);
   report.interactions.push('Expired move snapshot cannot prepare execution');
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);report.result='pass';fs.writeFileSync(path.join(dir,'review-results.json'),JSON.stringify(report,null,2)+'\n');combined.sprints.push({sprint:n,screens:manifest.length,variants:report.variants.length,interactions:report.interactions.length});console.log(JSON.stringify(combined.sprints.at(-1)));
 }
 combined.result='pass';fs.writeFileSync(path.join(__dirname,'batch-11-14-review-results.json'),JSON.stringify(combined,null,2)+'\n');await browser.close();console.log('PASS: 75 screens across Sprints 11–14');
})().catch(e=>{console.error(e);process.exit(1)});
