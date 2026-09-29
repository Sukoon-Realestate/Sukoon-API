import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  for (final direction in TextDirection.values) {
    for (final scale in [1.0, 2.0]) {
      testWidgets('app bar owns title, back and actions: $direction $scale', (
        tester,
      ) async {
        tester.view.physicalSize = const Size(320, 640);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        int actionCalls = 0;
        await tester.pumpWidget(_app(direction: direction, scale: scale));
        Go.to<void>(
          AppScaffold(
            title: 'Property details',
            actions: [
              IconButton(
                tooltip: 'Settings',
                onPressed: () => actionCalls++,
                icon: const Icon(Icons.settings),
              ),
            ],
            body: const Text('Property content'),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Property details'), findsOneWidget);
        expect(
          find.descendant(
            of: find.byType(AppBar),
            matching: find.text('Property details'),
          ),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: find.byType(AppBar),
            matching: find.byType(SokoonBackButton),
          ),
          findsOneWidget,
        );
        await tester.tap(find.byTooltip('Settings'));
        expect(actionCalls, 1);
        await tester.tap(find.byType(SokoonBackButton));
        await tester.pumpAndSettle();
        expect(find.text('Root'), findsOneWidget);
        expect(find.text('Property content'), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('custom back changes a flow step without popping the route', (
    tester,
  ) async {
    int previousSteps = 0;
    await tester.pumpWidget(_app());
    Go.to<void>(
      AppScaffold(
        title: 'Photos',
        onBack: () => previousSteps++,
        body: const Text('Property flow'),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byType(SokoonBackButton));
    await tester.pumpAndSettle();
    expect(previousSteps, 1);
    expect(find.text('Property flow'), findsOneWidget);
  });

  testWidgets('busy flows disable the app bar back action', (tester) async {
    int previousSteps = 0;
    await tester.pumpWidget(_app());
    Go.to<void>(
      AppScaffold(
        title: 'Saving',
        onBack: () => previousSteps++,
        isBackEnabled: false,
        body: const Text('Pending request'),
      ),
    );
    await tester.pumpAndSettle();
    final button = tester.widget<IconButton>(
      find.descendant(
        of: find.byType(SokoonBackButton),
        matching: find.byType(IconButton),
      ),
    );
    expect(button.onPressed, isNull);
    await tester.tap(find.byType(SokoonBackButton));
    expect(previousSteps, 0);
    expect(find.text('Pending request'), findsOneWidget);
  });

  testWidgets('default app bar back respects the screen pop guard', (
    tester,
  ) async {
    bool blocked = false;
    await tester.pumpWidget(_app());
    Go.to<void>(
      PopScope(
        canPop: false,
        onPopInvokedWithResult: (didPop, _) => blocked = !didPop,
        child: const AppScaffold(title: 'Edit', body: Text('Unsaved form')),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byType(SokoonBackButton));
    await tester.pumpAndSettle();
    expect(blocked, isTrue);
    expect(find.text('Unsaved form'), findsOneWidget);
  });
}

Widget _app({TextDirection direction = TextDirection.ltr, double scale = 1}) =>
    ScreenUtilInit(
      designSize: const Size(360, 690),
      enableScaleWH: () => false,
      enableScaleText: () => false,
      builder: (_, _) => MaterialApp(
        navigatorKey: Go.navigatorKey,
        theme: SokounTheme.light,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(scale)),
          child: Directionality(textDirection: direction, child: child!),
        ),
        home: const Scaffold(body: Text('Root')),
      ),
    );
