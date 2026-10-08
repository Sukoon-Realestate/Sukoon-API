# ==============================
# Flutter Makefile
# ==============================

.PHONY: clean run apk ios upgrade handlePods openXcode translations gradleFix clearGradleCache \
        buildIos distribute distributeAndroid flutterfireSetup demo demoSetup demoCapture buildWeb deploy checkWeb previewWeb

FLUTTER ?= flutter
WEB_BUILD_ARGS ?=

## Install the local video renderer and browsers for release checks.
demoSetup:
	npm ci --prefix tool/demo_video
	cd tool/demo_video && npx playwright install chromium webkit

## Capture sample tenant and owner screens from the current Sokoun widgets.
demoCapture:
	cd ../sokoun_app && $(FLUTTER) test --no-pub tool/capture_landing_demo_test.dart

## Regenerate the 40 second demo MP4 and its landing page poster.
demo: demoCapture
	npm run --prefix tool/demo_video render

# Clean Flutter build and get packages
clean:
	flutter clean && flutter pub get

# Upgrade Flutter packages
upgrade:
	flutter pub upgrade

# Install flutterfire CLI (fixes iOS "flutterfire: command not found" build phase failure)
flutterfireSetup:
	dart pub global activate flutterfire_cli

# Generate translations
translations:
	dart run generate/strings/main.dart

## Build a fresh release with local renderer resources and only the fonts this site uses.
buildWeb:
	$(FLUTTER) clean
	$(FLUTTER) pub get
	$(FLUTTER) build web --release --no-web-resources-cdn --no-wasm-dry-run $(WEB_BUILD_ARGS)
	dart tool/optimize_web_build.dart

## Verify release playback and startup in Chromium and WebKit against a local URL.
checkWeb:
	npm run --prefix tool/demo_video check-web -- $(if $(URL),$(URL),http://127.0.0.1:4177)

## Serve the release with compression and byte-range support for video.
previewWeb:
	node tool/serve_web.cjs

deploy: buildWeb
	firebase deploy --only hosting
