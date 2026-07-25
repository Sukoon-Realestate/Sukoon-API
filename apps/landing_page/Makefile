# ==============================
# Flutter Makefile
# ==============================

.PHONY: clean run apk ios upgrade handlePods openXcode translations gradleFix clearGradleCache \
        buildIos distribute distributeAndroid flutterfireSetup

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
