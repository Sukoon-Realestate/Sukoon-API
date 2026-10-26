(() => {
  const key=window.galleryCollection;
  const send=message=>parent.postMessage({gallery:true,key,...message},'*');
  let applying=false;
  const section=document.querySelector('.atlas');
  function size(){const height=Math.ceil(section.getBoundingClientRect().height);if(height>0)send({type:'height',height})}
  new ResizeObserver(size).observe(section);
  document.fonts.ready.then(size);
  window.addEventListener('resize',size);
  function positionDialogs(){
    const frame=window.frameElement;
    if(!frame)return;
    const dialogs=[...document.querySelectorAll('dialog[open]')];
    if(!dialogs.length){send({type:'modal',open:false});return}
    const bounds=frame.getBoundingClientRect();
    const top=Math.max(12,Math.min(bounds.height-parent.innerHeight+20,-bounds.top+16));
    parent.scrollBy({top:bounds.top+top-16,behavior:'instant'});
    dialogs.forEach(dialog=>{
      dialog.style.position='fixed';dialog.style.top=top+'px';dialog.style.bottom='auto';dialog.style.margin='0 auto';dialog.style.maxHeight=Math.max(220,parent.innerHeight-32)+'px';
      const body=dialog.querySelector('.focus-body');if(body)body.style.maxHeight=Math.max(160,parent.innerHeight-120)+'px';
    });
    send({type:'modal',open:!!document.querySelector('dialog[open]')});
  }
  document.querySelectorAll('dialog').forEach(dialog=>new MutationObserver(positionDialogs).observe(dialog,{attributes:true,attributeFilter:['open']}));
  const routes={"contract-document":"S175","my-reviews":"S198","media-next":"S61","visit-chat":"S99","subscriptions":"S88","invoices":"S86","chat-policy":"S92","owner-revenue":"S65","my-housing":"S137",'register':'S21','forgot':'S22','upload':'S23','account-summary':'S42','support-new':'S44','support-tickets':'S46','legal':'S47','business-policies':'S48','guide-settings':'S49','feedback':'S44'};
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');
    if(button?.dataset.mode&&!applying)send({type:'theme',mode:button.dataset.mode});
    let target=button?.dataset.go||((button?.dataset.action==='workspace'&&['student','company'].includes(button?.dataset.value))?(button.dataset.value==='student'?'S219':'S249'):routes[button?.dataset.action]);
    if(target&&!String(target).startsWith('S'))target='S'+String(target).padStart(2,'0');
    if(target&&!document.getElementById(target)){event.preventDefault();event.stopImmediatePropagation();send({type:'focus',id:target});return}
    const anchor=event.target.closest('a');if(anchor){anchor.target='_blank';anchor.rel='noopener'}
  },true);
  window.addEventListener('message',event=>{
    if(event.source!==parent||!event.data?.gallery)return;
    const message=event.data;
    if(message.type==='ping'){size();send({type:'ready'});return}
    if(message.type==='theme'){
      applying=true;document.querySelector(`button[data-mode="${message.mode}"]`)?.click();applying=false;
    }
    if(message.type==='focus'){
      const el=document.getElementById(message.id);if(!el)return;
      const button=el.querySelector('[data-open],[data-focus]');button?.click();positionDialogs();
    }
    if(message.type==='locate'){
      const el=document.getElementById(message.id);if(el)send({type:'located',id:message.id,top:el.getBoundingClientRect().top});
    }
  });
  size();send({type:'ready'});
})();
