// Runs in <head> before first paint. Shows the logo splash until the page has
// loaded: at least MIN_MS so it never just flickers, at most MAX_MS so a slow
// asset can't hold the page hostage. "out" fades it, then the flag is dropped.
const MIN_MS = 600;
const MAX_MS = 3000;

export const loadingInitScript = `try{var d=document.documentElement,s=performance.now();d.dataset.loading="on";var done=function(){if(d.dataset.loading!=="on")return;setTimeout(function(){d.dataset.loading="out";setTimeout(function(){delete d.dataset.loading},600)},Math.max(0,${MIN_MS}-(performance.now()-s)))};if(document.readyState==="complete")done();else addEventListener("load",done);setTimeout(done,${MAX_MS})}catch(e){}`;
