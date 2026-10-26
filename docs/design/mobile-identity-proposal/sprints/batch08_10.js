// Extra interactions are scoped to this illustrative batch; never call a server.
(()=>{
 function error(form,message){let el=form.querySelector('[data-local-error]');if(!el){el=document.createElement('p');el.dataset.localError='';el.setAttribute('role','alert');form.prepend(el)}el.textContent=message;el.scrollIntoView({block:'nearest'})}
 document.addEventListener('submit',event=>{
  const f=event.target;if(!f.matches('[data-form=batch-form]'))return;const fields=f.elements;
  let message='';
  if(fields.capacity&&(!Number.isInteger(Number(fields.capacity.value))||Number(fields.capacity.value)<2))message='السعة لازم تكون عددًا صحيحًا لا يقل عن ٢.';
  if(f.dataset.kind==='rental-summary'&&!fields.shareBooking.checked&&fields.invoice.value==='0'&&fields.receipt.value==='0')message='اختار محتوى واحدًا على الأقل للمشاركة.';
  if(fields.expiry&&fields.expiry.value&&new Date(fields.expiry.value+'T23:59:59')<=new Date())message='اختار موعد انتهاء في المستقبل.';
  if(message){event.preventDefault();event.stopImmediatePropagation();error(f,message)}else f.querySelector('[data-local-error]')?.remove();
 },true);
 document.addEventListener('click',event=>{
  const remove=event.target.closest('[data-batch-line-remove]');if(remove){event.preventDefault();remove.closest('.settlement-line').remove();return}
  const add=event.target.closest('[data-batch-line-add]');if(!add)return;
  event.preventDefault();const f=add.closest('form'),amount=f.elements.lineAmount,description=f.elements.lineDescription;
  if(!amount.reportValidity()||!description.value.trim()){error(f,'اكتب مبلغًا موجبًا ووصفًا واضحًا للبند.');return}
  f.querySelector('[data-local-error]')?.remove();const line=document.createElement('div');line.className='settlement-line';const text=document.createElement('b');text.textContent=description.value.trim()+' · '+amount.value+' ج.م';const button=document.createElement('button');button.type='button';button.className='textbtn';button.dataset.batchLineRemove='';button.textContent='حذف';line.append(text,button);f.querySelector('[data-settlement-lines]').append(line);
 },true);
})();
