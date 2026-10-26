// Final-batch interactions are entirely local and use text nodes for supplied data.
(()=>{
 const error=(form,message)=>{let el=form.querySelector('[data-final-error]');if(!el){el=document.createElement('p');el.dataset.finalError='';el.setAttribute('role','alert');form.prepend(el)}el.textContent=message;el.scrollIntoView({block:'nearest'})};
 document.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.dataset.action==='final-state'){
   event.preventDefault();const phone=button.closest('.phone'),select=document.querySelector('[data-state="'+phone.dataset.screen+'"]');select.value=button.dataset.variant;select.dispatchEvent(new Event('change',{bubbles:true}));return;
  }
  if(button.dataset.action==='final-csv'){
   const form=button.closest('form'),preview=form.querySelector('[data-csv-preview]'),csv=form.elements.csv.value.trim();preview.replaceChildren();
   const rows=csv.split(/\r?\n/).map(row=>row.split(','));const required=['name','email','employee_code'];
   const status=document.createElement('p');status.className='csv-feedback';
   if(rows.length<2||required.some((name,i)=>rows[0][i]?.trim()!==name)||rows.slice(1).some(row=>row.length!==3||row.some(v=>!v.trim()))){status.textContent='راجع عناوين الأعمدة الثلاثة والقيم في كل صف. نموذج المعاينة يدعم CSV بسيطًا فقط.';status.classList.add('error');preview.append(status);return}
   const codes=rows.slice(1).map(row=>row[2].trim());
   if(new Set(codes).size!==codes.length){status.textContent='فيه أكواد موظفين مكررة؛ راجع الصفوف قبل التجهيز.';status.classList.add('error');preview.append(status);return}
   status.textContent=String(rows.length-1)+' صفوف للمراجعة محليًا؛ لم يتم تجهيز أو إرسال سجلات.';preview.append(status);
   for(const row of rows.slice(1)){const el=document.createElement('div');el.className='csv-row';el.textContent=row.join(' · ');preview.append(el)}
  }
 },true);
 document.addEventListener('change',event=>{if(event.target.name==='pricingRule'){const box=event.target.form?.querySelector('[data-tier-fields]');if(box){box.hidden=event.target.value==='0';box.disabled=box.hidden}}});
 document.addEventListener('submit',event=>{
  const form=event.target;if(!form.matches('[data-form=batch-form]'))return;const f=form.elements;let message='';
  if(f.unitCodes){const codes=f.unitCodes.value.split(/\r?\n/).map(v=>v.trim()).filter(Boolean);if(!codes.length||new Set(codes).size!==codes.length)message='كل وحدة لازم يكون لها كود مختلف وغير فارغ.'}
  if(f.minimumCompletion&&(Number(f.minimumCompletion.value)<1||Number(f.minimumCompletion.value)>3||!Number.isInteger(Number(f.minimumCompletion.value))))message='العدد في هذا المثال لازم يكون من ١ إلى ٣ مشاركين.';
  if(f.minimumQuantity&&(!Number.isInteger(Number(f.minimumQuantity.value))||Number(f.minimumQuantity.value)<1||Number(f.minimumQuantity.value)>3))message='الحد الأدنى في هذا المثال من ١ إلى ٣ وحدات.';
  if(f.pricingRule&&f.pricingRule.value!=='0'&&(!Number.isInteger(Number(f.threshold.value))||Number(f.threshold.value)<2||Number(f.threshold.value)>3||Number(f.rate.value)>3500))message='راجع حد التسعير والسعر؛ السعر لا يتجاوز الأساسي في هذا المثال.';
  if(f.listName&&f.listName.value.trim().length>120)message='اسم القائمة لا يتجاوز ١٢٠ حرفًا.';
  if(f.expiry&&new Date(f.expiry.value+'T23:59:59')<=new Date())message='اختار موعد انتهاء في المستقبل.';
  if(message){event.preventDefault();event.stopImmediatePropagation();error(form,message)}else form.querySelector('[data-final-error]')?.remove();
 },true);
})();
