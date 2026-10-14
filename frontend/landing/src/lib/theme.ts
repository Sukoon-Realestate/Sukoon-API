export const THEME_STORAGE_KEY = "sukoon-theme";

// Runs in <head> before first paint: a saved choice wins, otherwise follow the OS.
export const themeInitScript = `try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t}catch(e){}`;
