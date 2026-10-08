# ==============================
# Flutter Makefile
# ==============================

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help clean run apk ipa appbundle ios upgrade \
	handlePods openXcode flutterfireSetup translations \
	architectureCheck accountCheck accountUiReview freeFeaturesCheck freeFeaturesUiReview featureToolsCheck featureToolsUiReview mobileBackendCheck mainJourneyCheck mainJourneyUiReview gradleFix clearGradleCache buildIos distribute \
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
	@echo "  make accountCheck"
	@echo "  make accountUiReview REVIEW_DIR=/tmp/sokoun-account-ui"
	@echo "  make freeFeaturesCheck"
	@echo "  make freeFeaturesUiReview FREE_REVIEW_DIR=/tmp/sokoun-free-after"
	@echo "  make featureToolsCheck"
	@echo "  make mobileBackendCheck"
	@echo "  make mainJourneyCheck"
	@echo "  make mainJourneyUiReview JOURNEY_REVIEW_DIR=/tmp/sokoun-main-flow-after"
	@echo "  make featureToolsUiReview TOOLS_REVIEW_DIR=/tmp/sokoun-tools-after"
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
	flutter run --flavor dev

# Build Android APK
apk:
	flutter build apk --split-per-abi --flavor prod

# Build Android App Bundle
appbundle:
	flutter build appbundle --flavor prod

# Build iOS IPA
ipa:
	flutter build ipa --flavor prod

# Build iOS application without IPA
ios:
	flutter build ios --flavor prod

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

## Verify Profile, Settings and Support architecture, behavior and layouts.
accountCheck:
	flutter analyze --no-pub lib/features/shared/profile lib/features/shared/support lib/features/shared/public_pages lib/features/main_view/presentation/models/home_tab.dart lib/features/shared/notifications/presentation/notification_navigation.dart
	flutter test --no-pub test/profile_flow_test.dart test/profile_settings_support_test.dart test/workspace_navigation_test.dart test/feature_architecture_test.dart
	flutter test --no-pub test/mobile_dev_handoff_integration_test.dart --plain-name='owner Profile opens API-backed revenue'

REVIEW_DIR ?= /tmp/sokoun-account-ui
## Run responsive account checks and export Arabic screenshots for UI review.
accountUiReview:
	flutter test --no-pub test/profile_settings_support_test.dart --dart-define=ACCOUNT_UI_REVIEW_DIR=$(REVIEW_DIR)

## Check all app flows, including persistence, booking conflicts, and architecture.
freeFeaturesCheck:
	flutter analyze --no-pub --no-fatal-infos --no-fatal-warnings
	flutter test --no-pub

FREE_REVIEW_DIR ?= /tmp/sokoun-free-after
## Render the free features in Arabic/English, both themes, six widths and three text sizes.
freeFeaturesUiReview:
	flutter test --no-pub test/free_features_ui_review_test.dart --dart-define=FREE_UI_REVIEW_DIR=$(FREE_REVIEW_DIR)

## Verify free feature tools, data contracts, flows and architecture.
featureToolsCheck:
	flutter analyze --no-pub lib/features/shared/premium lib/features/shared/digital_leases lib/features/shared/rent_management lib/features/owner/promotions lib/features/owner/advanced_analytics lib/features/owner/ai_assistant lib/features/tenant/premium_alerts test/feature_tools_contracts_test.dart test/feature_tools_flows_test.dart test/feature_tools_ui_review_test.dart test/helpers/feature_tools_test_dependencies.dart
	flutter test --no-pub test/feature_tools_contracts_test.dart test/feature_tools_flows_test.dart test/feature_tools_ui_review_test.dart test/feature_architecture_test.dart

TOOLS_REVIEW_DIR ?= /tmp/sokoun-tools-after
## Render free tool workflows in both languages and themes across six widths and three text scales.
featureToolsUiReview:
	flutter test --no-pub test/feature_tools_ui_review_test.dart --dart-define=FEATURE_TOOLS_UI_REVIEW_DIR=$(TOOLS_REVIEW_DIR)

## Verify the implemented mobile handoff, identities, retries and feature architecture.
mobileBackendCheck:
	flutter test --no-pub test/mobile_all_features_backend_handoff_test.dart test/feature_tools_contracts_test.dart test/feature_tools_flows_test.dart test/chat_api_contract_test.dart test/chat_thread_cubit_test.dart test/chat_flow_test.dart test/rental_offers_requests_test.dart test/rental_listing_categories_test.dart test/feature_architecture_test.dart

## Verify contextual main journeys, resource/cache boundaries and responsive layouts.
mainJourneyCheck:
	flutter analyze --no-pub --no-fatal-infos --no-fatal-warnings
	flutter test --no-pub test/main_journey_features_test.dart test/main_journey_ui_review_test.dart test/feature_tools_contracts_test.dart test/feature_tools_flows_test.dart test/feature_architecture_test.dart

JOURNEY_REVIEW_DIR ?= /tmp/sokoun-main-flow-after
## Render main app placements in both languages/themes, six widths and three text sizes.
mainJourneyUiReview:
	flutter test --no-pub test/main_journey_ui_review_test.dart --dart-define=MAIN_JOURNEY_UI_REVIEW_DIR=$(JOURNEY_REVIEW_DIR)

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
