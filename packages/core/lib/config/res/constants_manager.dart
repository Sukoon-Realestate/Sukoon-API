part of 'config_imports.dart';

final GetIt injector = GetIt.instance;

class ConstantManager {
  static const String bundleId = 'com.app.sokoon.real.estate';
  static const String devBundleId = 'com.app.sokoon.real.estate.dev';
  static const String appName = 'سكون';
  static const String defaultAvatar =
      'https://share.google/images/xqtQr0B9c0ROYtxeG';
  static const String fontFamily = 'packages/melos_core/Tajawal';
  static const String riyalFontFamily = 'packages/melos_core/Riyal';
  static const String projectName = 'سكون';
  static const int splashTimer = 3000;
  static const String baseUrl = 'https://str-sa.com/api/v1/';
  static const String testUrl = 'https://str-sa.4hoste.com/api/v1/';

  static String socketUrl =
      'a'; // default fallback; overridden from Remote Config at startup

  static const int zegoAppId = 509026631;
  static const String zegoAppSign =
      'abd4c5e860e63439d4887862a9c14d08fd1b5991fc7fd9ca69e79ee347a6e17e';

  // static const int zegoAppId = 1545294325;
  // static const String zegoAppSign = 'dd246a143dd5f0c30fa5d5e2bbf7f46a579c517bdf86b2d61b5d13574eb9fd56';

  static const int paginationFirstPage = 1;
  static const int paginationPageSize = 10;
  static const String emptyText = '';
  static const int zero = 0;
  static const double zeroAsDouble = 0.0;
  static const int pinCodeFieldsCount = 4;
  static const int maxLines = 4;
  static const double snackbarElevation = 4;
  static const int snackbarDuration = 4;
  static const int connectTimeoutDuration = 120;
  static const int recieveTimeoutDuration = 120;
  static const double customImageSliderAsepctRatio = 3;
  static const String ar = 'ar';
  static const String en = 'en';
  static const String arabic = 'العربية';
  static const String english = 'English';
  static String saudiArabCountryCode =
      Languages.currentLanguage.languageCode == 'ar' ? '966+' : '+966';
  static const int pgSize = 10;
  static String platform = Platform.isAndroid ? 'android' : 'ios';
  static const int pgFirst = 1;
  static const double cardElevation = 1;
  static const int rateCount = 5;
  static const double minRateCount = 1;
  static BorderRadius buttonBorderRadius = BorderRadius.circular(40.r);
  static double buttonBorderRadiusNumber = 10.r;
}

class CacheConstant {
  static const String onBoardingSubmission = "onBoardingSubmission";
  static const String isLoggedIn = "isLoggedIn";
  static const String lastSeenWhatsNewVersion = "lastSeenWhatsNewVersion";
}

class Styles {
  static TextStyle bold16 = TextStyle(
    fontSize: 16.sp,
    fontWeight: FontWeight.bold,
    fontFamily: ConstantManager.fontFamily,
  );
}
