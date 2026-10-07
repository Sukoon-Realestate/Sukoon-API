# ==============================
# Flutter Makefile
# ==============================

.PHONY: clean run apk ios upgrade handlePods openXcode translations gradleFix clearGradleCache \
        buildIos distribute distributeAndroid flutterfireSetup demo demoSetup demoCapture

FLUTTER ?= flutter

## Install the local video renderer and its Chromium browser.
demoSetup:
	npm ci --prefix tool/demo_video
	cd tool/demo_video && npx playwright install chromium

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

deploy:
	flutter clean && flutter pub get && flutter build web && firebase deploy --only hosting
