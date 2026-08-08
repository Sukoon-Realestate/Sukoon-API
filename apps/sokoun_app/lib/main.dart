import 'dart:developer';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_remote_config/firebase_remote_config.dart';
import 'package:flutter/foundation.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/helpers/nsfw_detector.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/fire_store.dart';
import 'package:melos_core/core/shared/Functions/setup_service_locators.dart';
import 'package:melos_core/core/shared/bloc_observer.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:sokoun_app/app.dart';

import 'firebase_options.dart' as dev;
import 'firebase_options_dev.dart' as prod;

void main() async {
  Helpers.changeStatusbarColor(statusBarColor: AppColors.white);
  Bloc.observer = AppBlocObserver();
  WidgetsFlutterBinding.ensureInitialized();
  await Future.wait([
    EasyLocalization.ensureInitialized(),
    CacheStorage.init(),
    ObjectBoxCacheService.init(),
    ScreenUtil.ensureScreenSize(),
  ]);
  await _initializeFirebaseApp();
  await fetchBaseUrl();
  await NsfwDetectorHelper.init();
  setUpServiceLocator();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  if (kReleaseMode) {
    ErrorWidget.builder = (FlutterErrorDetails details) {
      if (FireStoreService.isInitialized && kReleaseMode) {
        FireStoreService.instance.storeError(details.exceptionAsString());
      }

      return const ExceptionView();
    };
  }

  runApp(
    EasyLocalization(
      supportedLocales: Languages.supportedLocales,
      path: Languages.translationsPath,
      saveLocale: true,
      startLocale: Languages.arabic.locale,
      fallbackLocale: Languages.arabic.locale,
      child: const Sokoon(),
    ),
  );
}

void _changeFireStoreAvailability(bool enable) {
  if (enable) {
    FireStoreService.instance.enableService();
  } else {
    FireStoreService.instance.disableService();
  }
}

Future<bool> fetchBaseUrl() async {
  try {
    final remoteConfig = FirebaseRemoteConfig.instance;

    await remoteConfig.setConfigSettings(
      RemoteConfigSettings(
        fetchTimeout: const Duration(seconds: 10),
        minimumFetchInterval: Duration.zero,
      ),
    );
    await remoteConfig.setDefaults(const <String, dynamic>{
      SecureLocalVariableKeys.minAppVersionKey: '',
    });

    await remoteConfig.fetchAndActivate();

    if (kReleaseMode) {
      final bool fireStoreAvailabilityVal = remoteConfig.getBool(
        SecureLocalVariableKeys.fireStoreAvailabilityKey,
      );
      _changeFireStoreAvailability(fireStoreAvailabilityVal);
      log('the fire store availability is $fireStoreAvailabilityVal');
    }

    final String prodBaseUrl = remoteConfig.getString(
      SecureLocalVariableKeys.baseUrlKey,
    );
    final String devBaseUrl = remoteConfig.getString(
      SecureLocalVariableKeys.devBaseUrlKey,
    );
    final String socetIoUrl = remoteConfig.getString(
      SecureLocalVariableKeys.socetIoUrl,
    );
    final String minAppVersion = remoteConfig
        .getString(SecureLocalVariableKeys.minAppVersionKey)
        .trim();

    log('the prod base url is $prodBaseUrl');
    log('the dev base url is $devBaseUrl');
    log('the socket url is $socetIoUrl');
    log(
      'the minimum app version is '
      '${minAppVersion.isEmpty ? 'not configured' : minAppVersion}',
    );
    RemoteConfigValues.setMinAppVersion(minAppVersion);

    if (socetIoUrl.isNotEmpty) {
      await SecureStorage.write(SecureLocalVariableKeys.socetIoUrl, socetIoUrl);
    }

    if (prodBaseUrl.isEmpty && devBaseUrl.isEmpty) {
      return false;
    }

    if (prodBaseUrl.isNotEmpty) {
      await SecureStorage.write(
        SecureLocalVariableKeys.baseUrlKey,
        prodBaseUrl,
      );
    }
    if (devBaseUrl.isNotEmpty) {
      await SecureStorage.write(
        SecureLocalVariableKeys.devBaseUrlKey,
        devBaseUrl,
      );
    }

    return true;
  } catch (e) {
    log('the error is $e');
    return false;
  }
}

Future<void> _initializeFirebaseApp() async {
  final firebaseOptions = switch (appFlavor) {
    'dev' => dev.DefaultFirebaseOptions.currentPlatform,
    'prod' => prod.DefaultFirebaseOptions.currentPlatform,
    _ => () {
      log(
        'Unknown/empty appFlavor "$appFlavor" — defaulting Firebase to production options',
      );
      return prod.DefaultFirebaseOptions.currentPlatform;
    }(),
  };
  await Firebase.initializeApp(options: firebaseOptions);
}
