import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/auth/screens/login_screen.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('builds Sokoon login screen from shared widgets', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, child) {
          return const MaterialApp(home: LoginScreen());
        },
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.byType(SokoonEmailField), findsOneWidget);
    expect(find.byType(SokoonPasswordField), findsOneWidget);
    expect(find.byType(SokoonGoogleSignInButton), findsOneWidget);
    expect(find.byType(SokoonFacebookSignInButton), findsOneWidget);
    expect(find.byType(SokoonAppleSignInButton), findsOneWidget);
  });
}
