import 'dart:developer';
import 'package:appsflyer_sdk/appsflyer_sdk.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import '../../shared/models/user_models/user_model.dart';
import 'events.dart';

class AppyFlyerHelper{
  static late final AppsflyerSdk _appsflyerSdk;
  static bool _isInitialized = false;
  static bool _uninstallListenerAttached = false;

  static Future<void> init()async{
    final AppsFlyerOptions appsFlyerOptions = AppsFlyerOptions(
      afDevKey: 'StWx8Em3WFohBgA9vtdoT9',
      appId: '6756270317',
      showDebug: kDebugMode,
      timeToWaitForATTUserAuthorization: 50, // for iOS 14.5
      // appInviteOneLink: oneLinkID, // Optional field
      // disableAdvertisingIdentifier: false, // Optional field
      // disableCollectASA: false, //Optional field
      manualStart: true, // required so startSDK() actually starts the SDK and fires onSuccess/onError
    ); // Optional field

    _appsflyerSdk = AppsflyerSdk(appsFlyerOptions);
    await _appsflyerSdk.initSdk(
        registerConversionDataCallback: true,
        registerOnAppOpenAttributionCallback: true,
        registerOnDeepLinkingCallback: true
    );

    _appsflyerSdk.startSDK(
      onSuccess: () {
        log("AppsFlyer SDK initialized successfully.");
      },
      onError: (int errorCode, String errorMessage) {
        log("Error initializing AppsFlyer SDK: Code $errorCode - $errorMessage");
      },
    );
    _isInitialized = true;
    _handleDeepLinking();
  }

  static void setCustomer(){
    _appsflyerSdk.setCustomerUserId(UserModel.currentUser?.id.toString()??'0');
  }

  static Future<void> enableUninstallMeasurement()async{
    await _registerUninstallToken();
    if (_uninstallListenerAttached) return;
    _uninstallListenerAttached = true;
    FirebaseMessaging.instance.onTokenRefresh.listen((_) => _registerUninstallToken());
  }

  static Future<void> _registerUninstallToken()async{
    if (!_isInitialized) return;
    try {
      final String? token = await FirebaseMessaging.instance.getToken();
      if (token == null || token.isEmpty) return;
      _appsflyerSdk.updateServerUninstallToken(token);
      log("AppsFlyer uninstall token registered.");
    } catch (e) {
      log("Error registering AppsFlyer uninstall token: $e");
    }
  }

  static void _handleDeepLinking(){
    _appsflyerSdk.onDeepLinking((DeepLinkResult dp) {
      switch (dp.status) {
        case Status.FOUND:
          log("deep link value: ${dp.deepLink?.deepLinkValue}");
          break;
        case Status.NOT_FOUND:
          log("deep link not found");
          break;
        case Status.ERROR:
          log("deep link error: ${dp.error}");
          break;
        case Status.PARSE_ERROR:
          log("parsing error");
          break;
      }
    });
  }

  static Future<void> logEvent(FlyerEvents event)async{
    await _appsflyerSdk.logEvent(event.name, {
      'id' : UserModel.currentUser?.id,
      'name' : UserModel.currentUser?.name,
      'phone' : UserModel.currentUser?.phone,
      'gender' : UserModel.currentUser?.gender,
      'type' : UserModel.currentUser?.type,
    });
  }
}