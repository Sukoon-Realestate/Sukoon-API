import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';

void main() {
  testWidgets('loads the splash logo from a non-empty packaged asset', (
    tester,
  ) async {
    await tester.pumpWidget(
      ScreenUtilInit(
        designSize: const Size(360, 690),
        builder: (context, child) =>
            const MaterialApp(home: Scaffold(body: SplashLogo())),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(AppLogoWidget), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
