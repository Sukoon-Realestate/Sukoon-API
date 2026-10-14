// Runs in <head> before first paint: opt into entrance animations unless the
// visitor asked for reduced motion. A data attribute (not a class) so React
// never strips it when the root layout re-renders on a locale switch.
export const motionInitScript = `try{if(!matchMedia("(prefers-reduced-motion: reduce)").matches)document.documentElement.dataset.motion="on"}catch(e){}`;
