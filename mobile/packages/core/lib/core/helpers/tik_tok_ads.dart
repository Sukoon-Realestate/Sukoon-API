// import 'package:flutter/foundation.dart';
// import 'package:tiktok_events_sdk/tiktok_events_sdk.dart';
//
// import 'helpers.dart';
//
// class TikTokAdsHelper{
//   // iOS options example
//   final iosOptions = const TikTokIosOptions(
//     disableTracking: false, // true would disable ALL tracking
//     disableAutomaticTracking: true,
//     disableSKAdNetworkSupport: true,
//   );
//
// // Android options example
//   final androidOptions = const TikTokAndroidOptions(
//     enableAutoIapTrack: true, // enable IAP tracking
//     disableAdvertiserIDCollection: false,
//   );
//
//   void init()async{
//     await TikTokEventsSdk.initSdk(
//       androidAppId: Helpers.getBundleId,
//       tikTokAndroidId: '7643728081542184976',
//       iosAppId: Helpers.getBundleId,
//       tiktokIosId: '7646708941732642836',
//       // app secret TTX6m8tLKcJBEybIZeTDe2ejoSjExX6m
//       isDebugMode: kDebugMode,
//       logLevel: TikTokLogLevel.debug,
//       androidOptions: androidOptions,
//       iosOptions: iosOptions,
//     );
//   }
// // Pass these options to the initialize method
// }