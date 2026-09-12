# ==============================
# Flutter Makefile
# ==============================

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help clean run apk ipa appbundle ios upgrade \
	handlePods openXcode flutterfireSetup translations \
	architectureCheck gradleFix clearGradleCache buildIos distribute \
	distributeAndroid fingerPrint kill sha

# Show available commands
help:
	@echo "Available commands:"
	@echo "  make clean"
	@echo "  make run"
	@echo "  make apk"
	@echo "  make ipa"
	@echo "  make appbundle"
	@echo "  make ios"
	@echo "  make upgrade"
	@echo "  make handlePods"
	@echo "  make openXcode"
	@echo "  make flutterfireSetup"
	@echo "  make translations"
	@echo "  make architectureCheck"
	@echo "  make gradleFix"
	@echo "  make clearGradleCache"
	@echo "  make buildIos"
	@echo "  make distribute ARGS=\"...\""
	@echo "  make distributeAndroid ARGS=\"...\""
	@echo "  make fingerPrint"
	@echo "  make sha"
	@echo "  make kill"

# Clean Flutter build and install packages
clean:
	flutter clean
	flutter pub get

# Run the app
run:
	flutter run --flavor production

# Build Android APK
apk:
	flutter build apk --split-per-abi --flavor production

# Build Android App Bundle
appbundle:
	flutter build appbundle --flavor production

# Build iOS IPA
ipa:
	flutter build ipa --flavor production

# Build iOS application without IPA
ios:
	flutter build ios --flavor production

# Upgrade Flutter packages
upgrade:
	flutter pub upgrade

# Install CocoaPods dependencies
handlePods:
	cd ios && pod install --repo-update

# Open the iOS workspace in Xcode
openXcode:
	open ios/Runner.xcworkspace

# Install FlutterFire CLI
flutterfireSetup:
	dart pub global activate flutterfire_cli
	@echo "Add FlutterFire to PATH if needed:"
	@echo 'export PATH="$$PATH:$$HOME/.pub-cache/bin"'

# Generate translations
translations:
	cd ../.. && dart run generate/strings/main.dart

# Verify feature-layer architecture invariants
architectureCheck:
	flutter test --no-pub test/feature_architecture_test.dart

# Stop Gradle and remove lock files
gradleFix:
	@echo "Stopping Gradle daemons..."
	@cd android && ./gradlew --stop || true
	@echo "Killing Gradle processes..."
	@pkill -9 -f gradle || true
	@echo "Removing Gradle lock files..."
	@find android/.gradle -name "*.lock" -delete 2>/dev/null || true
	@find "$$HOME/.gradle" -name "*.lock" -delete 2>/dev/null || true
	@echo "Gradle locks cleared."

# Clear Gradle caches
clearGradleCache:
	rm -rf android/.gradle
	rm -rf "$$HOME/.gradle/caches"
	@echo "Gradle caches cleared."

# Upload iOS build
buildIos:
	sh upload_ios.sh

# Distribute iOS build
distribute:
	sh distribute_ios.sh $(ARGS)

# Distribute Android build
distributeAndroid:
	sh distribute_android.sh $(ARGS)

# Show signing key fingerprint
fingerPrint:
	keytool -list -v \
		-keystore android/app/key.jks \
		-storepass 123456

# Stop Dart processes
kill:
	@killall -9 dart || true

# Show Android signing report
sha:
	cd android && ./gradlew signingReport
