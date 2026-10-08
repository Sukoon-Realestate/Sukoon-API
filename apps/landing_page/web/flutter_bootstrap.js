{{flutter_js}}
{{flutter_build_config}}

// Serve the bundled renderer from Firebase alongside the app. This avoids
// waiting for another origin or failing when Google's CDN is unreachable.
_flutter.loader.load({
  config: {
    canvasKitBaseUrl: new URL('canvaskit/', document.baseURI).href,
  },
}).catch(error => console.error('Could not start Sokoun.', error));
