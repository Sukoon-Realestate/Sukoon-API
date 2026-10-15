export const THEME_STORAGE_KEY = "sukoon-theme";

// Runs in <head> before first paint: a saved choice wins, otherwise light.
export const themeInitScript = `try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="dark")t="light";document.documentElement.dataset.theme=t}catch(e){}`;
