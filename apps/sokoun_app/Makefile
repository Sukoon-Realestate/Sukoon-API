# ==============================
# Flutter Makefile
# ==============================

.PHONY: clean run apk ios upgrade handlePods openXcode translations gradleFix clearGradleCache \
        buildIos distribute distributeAndroid flutterfireSetup

# Clean Flutter build and get packages
clean:
	flutter clean && flutter pub get

# Run the app on a connected device
run:
	flutter run

# Build APK
apk:
	flutter build apk --split-per-abi --flavor production

ipa:
	flutter build ipa --flavor production

appbundle:
	flutter build appbundle --flavor production

# Build iOS (for macOS users with Xcode)
ios:
	flutter build ios

# Upgrade Flutter packages
upgrade:
	flutter pub upgrade

# Install & update CocoaPods
handlePods:
	cd ios && pod install && pod update && cd ..

# Open project in Xcode
openXcode:
	open ios/Runner.xcworkspace

# Install flutterfire CLI (fixes iOS "flutterfire: command not found" build phase failure)
flutterfireSetup:
	dart pub global activate flutterfire_cli

# Generate translations
translations:
	dart run generate/strings/main.dart

# Fix Gradle lock issues
gradleFix:
	@echo "Stopping Gradle daemons..."
	-cd android && ./gradlew --stop
	@echo "Killing Gradle and Java processes..."
	-pkill -9 -f gradle || true
	-pkill -9 -f java || true
	@echo "Removing lock files..."
	-find android/.gradle -name "*.lock" -delete 2>/dev/null || true
	-find ~/.gradle -name "*.lock" -delete 2>/dev/null || true
	@echo "Gradle locks cleared!"

clearGradleCache:
	rm -rf android/.gradle
	rm -rf ~/.gradle/caches

# Upload iOS build
buildIos:
	sh upload_ios.sh

# ==============================
# Firebase App Distribution
# ==============================

# Distribute iOS build — see distribute_ios.sh for all options
distribute:
	sh distribute_ios.sh $(ARGS)

# Distribute Android build — see distribute_android.sh for all options
distributeAndroid:
	sh distribute_android.sh $(ARGS)

fingerPrint:
	keytool -list -v -keystore android/app/key.jks -storepass 123456

kill:
	killall -9 dart
