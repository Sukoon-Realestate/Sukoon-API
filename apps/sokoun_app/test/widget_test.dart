import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/auth/screens/login_screen.dart';
import 'package:sokoun_app/features/auth/screens/otp_screen.dart';
import 'package:sokoun_app/features/auth/screens/register_screen.dart';
import 'package:sokoun_app/features/auth/screens/role_select_screen.dart';
import 'package:sokoun_app/features/auth/screens/welcome_screen.dart';
import 'package:sokoun_app/features/auth/screens/widgets/login/login_footer.dart';
import 'package:sokoun_app/features/auth/screens/widgets/otp/otp_code_field.dart';
import 'package:sokoun_app/features/auth/screens/widgets/otp/otp_resend_timer.dart';
import 'package:sokoun_app/features/auth/screens/widgets/role_select/role_option_card.dart';
import 'package:sokoun_app/features/auth/screens/widgets/welcome/welcome_center_card.dart';
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

  testWidgets('builds Sokoon welcome screen with three center cards', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(buildScreen(const WelcomeScreen()));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(WelcomeScreen), findsOneWidget);
    expect(find.byType(WelcomeCenterCard), findsNWidgets(3));
  });

  testWidgets('builds Sokoon role select screen with two role cards', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(buildScreen(const RoleSelectScreen()));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(RoleSelectScreen), findsOneWidget);
    expect(find.byType(RoleOptionCard), findsNWidgets(2));
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
