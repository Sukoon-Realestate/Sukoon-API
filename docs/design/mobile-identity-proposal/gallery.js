(() => {
  const collections=__COLLECTIONS__;
  const root=document.documentElement,media=matchMedia('(prefers-color-scheme: dark)');
  const frames=[...document.querySelectorAll('.collection-frame')];
  const loaded=new Set(),modals=new Set();
  let pendingFocus=null;
  let mode=new URLSearchParams(location.search).get('theme');
  if(!['light','dark','system'].includes(mode)){try{mode=localStorage.getItem('sukoon-proposal-theme')||'system'}catch{mode='system'}}
  if(!['light','dark','system'].includes(mode))mode='system';
  function send(frame,message){frame.contentWindow.postMessage({gallery:true,...message},'*')}
  function sync(){
    root.dataset.theme=mode==='system'?(media.matches?'dark':'light'):mode;root.dataset.mode=mode;
    document.querySelectorAll('[data-gallery-mode]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.galleryMode===mode)));
    document.querySelector('[data-gallery-theme-label]').textContent=mode==='system'?'المظهر يتبع إعداد الجهاز':'اختيار المظهر محفوظ';
    document.querySelector('.maplink').href='design-map.html?theme='+mode;
  }
  function setMode(value){mode=value;try{localStorage.setItem('sukoon-proposal-theme',mode)}catch{}sync();frames.forEach(frame=>send(frame,{type:'theme',mode}))}
  function reveal(key){document.querySelector('#collection-filter').value='all';document.querySelectorAll('.collection').forEach(section=>section.hidden=false)}
  function locate(id,focus=false){
    const collection=collections.find(c=>c.ids.includes(id));if(!collection)return;
    reveal(collection.key);const frame=frames.find(f=>f.dataset.collection===collection.key);
    // First place the destination near the viewport, then position its modal.
    document.getElementById(collection.key).scrollIntoView({behavior:'instant',block:'start'});
    if(focus)pendingFocus=id;send(frame,{type:'locate',id});
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-gallery-mode]');if(button)setMode(button.dataset.galleryMode);
    const jump=event.target.closest('.collection-jumps a');if(jump){const key=jump.hash.slice(1);reveal(key)}
  });
  document.querySelector('#collection-filter').addEventListener('change',event=>document.querySelectorAll('.collection').forEach(section=>section.hidden=event.target.value!=='all'&&section.id!==event.target.value));
  media.addEventListener('change',()=>{if(mode==='system')sync()});sync();
  window.addEventListener('message',event=>{
    const frame=frames.find(f=>f.contentWindow===event.source);const message=event.data;
    if(!frame||!message?.gallery||message.key!==frame.dataset.collection)return;
    if(message.type==='height'&&Number.isFinite(message.height)&&message.height>0&&message.height<100000){frame.style.height=message.height+'px';frame.dataset.ready='true'}
    if(message.type==='theme'&&['light','dark','system'].includes(message.mode))setMode(message.mode);
    if(message.type==='modal'){message.open?modals.add(message.key):modals.delete(message.key);document.body.style.overflow=modals.size?'hidden':''}
    if(message.type==='focus')locate(message.id,true);
    if(message.type==='located'){window.scrollTo({top:window.scrollY+frame.getBoundingClientRect().top+message.top-16,behavior:'instant'});if(pendingFocus===message.id){pendingFocus=null;send(frame,{type:'focus',id:message.id})}}
    if(message.type==='ready'){
      loaded.add(message.key);send(frame,{type:'theme',mode});
      if(loaded.size===frames.length){root.dataset.galleryReady='true';if(/^#S\d+$/.test(location.hash))locate(location.hash.slice(1))}
    }
  });
  frames.forEach(frame=>{frame.addEventListener('load',()=>send(frame,{type:'ping'}));send(frame,{type:'ping'})});
  window.addEventListener('hashchange',()=>{if(/^#S\d+$/.test(location.hash))locate(location.hash.slice(1))});
})();
