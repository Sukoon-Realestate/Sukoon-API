import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/shared_widgets/unauthenticated_sheet.dart';
import 'package:sokoun_app/features/main_view/presentation/screens/view.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity'),
          (_) async => ['wifi'],
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
          (_) async => null,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    registerHomePageTestDependencies();
    PackageInfo.setMockInitialValues(
      appName: 'Sokoun',
      packageName: 'test.sokoun',
      version: '1.0.0',
      buildNumber: '1',
      buildSignature: '',
    );
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  testWidgets('visitor can browse but private tabs present the sign-in gate', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await CacheStorage.delete('user');

    await tester.pumpWidget(_buildApp(const LoginScreen()));
    await tester.pumpAndSettle();

    final visitorButton = find.text('Sign in as visitor');
    await tester.ensureVisible(visitorButton);
    await tester.tap(visitorButton);
    await tester.pumpAndSettle();

    expect(find.byType(HomeScreen), findsOneWidget);
    expect(find.byType(UnauthenticatedSheet), findsNothing);
    tester
        .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
        .onDestinationSelected(1);
    await tester.pumpAndSettle();
    expect(find.byType(UnauthenticatedSheet), findsOneWidget);
  });

  testWidgets(
    'showUnAuthSheet presents the visitor gate and returns its action',
    (tester) async {
      UnauthenticatedSheetAction? selectedAction;

      await tester.pumpWidget(
        _buildApp(
          Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () async {
                  final sheetResult =
                      Helpers.showUnAuthSheet<UnauthenticatedSheetAction>();
                  selectedAction = await sheetResult;
                },
                child: const Text('Open visitor gate'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Open visitor gate'));
      await tester.pumpAndSettle();

      expect(find.byType(UnauthenticatedSheet), findsOneWidget);

      await tester.tap(find.byType(OutlinedButton));
      await tester.pumpAndSettle();

      expect(selectedAction, UnauthenticatedSheetAction.createAccount);
      expect(find.byType(UnauthenticatedSheet), findsNothing);
    },
  );
}

Widget _buildApp(Widget home) {
  return EasyLocalization(
    supportedLocales: const [Locale('en')],
    path: 'unused',
    assetLoader: const _AuthTestAssetLoader(),
    startLocale: const Locale('en'),
    fallbackLocale: const Locale('en'),
    child: ScreenUtilInit(
      designSize: const Size(390, 844),
      builder: (context, _) => MaterialApp(
        navigatorKey: Go.navigatorKey,
        localizationsDelegates: context.localizationDelegates,
        supportedLocales: context.supportedLocales,
        locale: context.locale,
        home: home,
      ),
    ),
  );
}

class _AuthTestAssetLoader extends AssetLoader {
  const _AuthTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return const {
      'forgot_password': 'Forgot password?',
      'login': 'Log in',
      'sign_in_as_visitor': 'Sign in as visitor',
      'welcome_back_to_sokoon': 'Welcome back to Sokoon',
      'email': 'Email',
      'password': 'Password',
      'or': 'Or',
      'do_not_have_an_account': 'Do not have an account',
      'sign_up': 'Sign up',
      'unauthenticated_sheet_title': 'Sign in to continue',
      'unauthenticated_sheet_description':
          'This feature requires an account so we can maintain security and trust',
      'create_account': 'Create Account',
    };
  }
}
