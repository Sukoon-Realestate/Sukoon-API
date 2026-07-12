import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/auth/screens/login_screen.dart';
import 'package:sokoun_app/features/auth/screens/otp_screen.dart';
import 'package:sokoun_app/features/auth/screens/register_screen.dart';
import 'package:sokoun_app/features/auth/screens/widgets/login/login_footer.dart';
import 'package:sokoun_app/features/auth/screens/widgets/otp/otp_code_field.dart';
import 'package:sokoun_app/features/auth/screens/widgets/otp/otp_resend_timer.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget buildScreen(Widget child) {
    return ScreenUtilInit(
      designSize: Size(ScreenSizes.width, ScreenSizes.height),
      builder: (context, _) {
        return MaterialApp(home: child);
      },
    );
  }

  testWidgets('builds Sokoon login screen from shared widgets', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(buildScreen(const LoginScreen()));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.byType(SokoonEmailField), findsOneWidget);
    expect(find.byType(SokoonPasswordField), findsOneWidget);
    expect(find.byType(SokoonGoogleSignInButton), findsOneWidget);
    expect(find.byType(SokoonFacebookSignInButton), findsOneWidget);
    expect(find.byType(SokoonAppleSignInButton), findsOneWidget);
    expect(find.byType(LoginFooter), findsOneWidget);
  });

  testWidgets('builds Sokoon register screen from shared fields', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(buildScreen(const RegisterScreen()));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(RegisterScreen), findsOneWidget);
    expect(find.byType(SokoonNameField), findsOneWidget);
    expect(find.byType(SokoonPhoneField), findsOneWidget);
    expect(find.byType(SokoonEmailField), findsOneWidget);
    expect(find.byType(SokoonPasswordField), findsOneWidget);
    expect(find.byType(SokoonPasswordConfirmationField), findsOneWidget);
  });

  testWidgets('builds Sokoon otp screen with code field and timer', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(buildScreen(const OtpScreen()));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(OtpScreen), findsOneWidget);
    expect(find.byType(OtpCodeField), findsOneWidget);
    expect(find.byType(OtpResendTimer), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
  });
}
