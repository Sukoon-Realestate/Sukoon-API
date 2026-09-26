import 'package:easy_localization/easy_localization.dart';
import 'package:easy_timer_count/easy_timer_count.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/auth/presentation/widgets/shared/auth_resend_timer.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    await CacheStorage.write('current_user_type', 'tenant');
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  testWidgets('shows the countdown until resend becomes available', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(_buildTimer(canResend: false));
    await tester.pump();

    expect(find.byType(EasyTimerCount), findsOneWidget);
    expect(find.textContaining('01:00'), findsOneWidget);

    await tester.pumpWidget(_buildTimer(canResend: true));
    await tester.pump();

    expect(find.byType(EasyTimerCount), findsNothing);
    expect(find.text('You can resend now'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

Widget _buildTimer({required bool canResend}) {
  return EasyLocalization(
    supportedLocales: const [Locale('en')],
    path: 'unused',
    assetLoader: const _TimerTestAssetLoader(),
    startLocale: const Locale('en'),
    fallbackLocale: const Locale('en'),
    child: ScreenUtilInit(
      designSize: const Size(390, 844),
      builder: (context, _) => MaterialApp(
        localizationsDelegates: context.localizationDelegates,
        supportedLocales: context.supportedLocales,
        locale: context.locale,
        home: Scaffold(
          body: AuthResendTimer(canResend: canResend, onTimerEnds: () {}),
        ),
      ),
    ),
  );
}

class _TimerTestAssetLoader extends AssetLoader {
  const _TimerTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return const {
      'resend_after': 'Resend after',
      'you_can_resend_code_now': 'You can resend now',
    };
  }
}
