import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/core/widgets/buttons/custom_app_buttons/loading_button.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  testWidgets(
    'fixed footer leaves the body visible and constrains tablet width',
    (tester) async {
      tester.view.physicalSize = const Size(1024, 768);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        _app(
          AppScaffold(
            showBackButton: false,
            contentWidth: SokounContentWidth.form,
            body: const Center(child: Text('Form content')),
            bottomBar: DefaultButton(title: 'Continue', onTap: () {}),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final footer = tester.getRect(find.byType(DefaultButton));
      final content = tester.getRect(find.text('Form content'));
      expect(footer.width, 520);
      expect(footer.height, greaterThanOrEqualTo(48));
      expect(footer.height, lessThan(120));
      expect(content.bottom, lessThan(footer.top));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('large labels grow, disabled buttons cannot submit', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    int calls = 0;
    await tester.pumpWidget(
      _app(
        Scaffold(
          body: Center(
            child: DefaultButton(
              title: 'Continue to confirm your property details',
              fontSize: 18,
              disabled: true,
              onTap: () => calls++,
            ),
          ),
        ),
        scale: 2,
      ),
    );
    await tester.tap(find.byType(ElevatedButton));
    expect(calls, 0);
    expect(tester.getSize(find.byType(DefaultButton)).height, greaterThan(48));
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'loading retains size, blocks duplicate taps and tolerates disposal',
    (tester) async {
      final pending = Completer<void>();
      int calls = 0;
      await tester.pumpWidget(
        _app(
          Scaffold(
            body: Center(
              child: LoadingButton(
                height: 48,
                idleWidget: const Text('Confirm this request'),
                loadingWidget: const CircularProgressIndicator(),
                call: (_) {
                  calls++;
                  return pending.future;
                },
              ),
            ),
          ),
        ),
      );
      final size = tester.getSize(find.byType(LoadingButton));
      await tester.tap(find.byType(ElevatedButton));
      await tester.pump();
      await tester.tap(find.byType(ElevatedButton));
      expect(calls, 1);
      expect(tester.getSize(find.byType(LoadingButton)), size);
      await tester.pumpWidget(const SizedBox.shrink());
      pending.complete();
      await tester.pump();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('keyboard insets keep a focused form and footer reachable', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final controller = TextEditingController();
    addTearDown(controller.dispose);
    await tester.pumpWidget(
      _app(
        AppScaffold(
          showBackButton: false,
          body: SingleChildScrollView(
            child: Column(
              children: [
                const SizedBox(height: 300),
                TextField(controller: controller),
              ],
            ),
          ),
          bottomBar: DefaultButton(title: 'Save', onTap: () {}),
        ),
      ),
    );
    await tester.enterText(find.byType(TextField), 'Retained input');
    tester.view.viewInsets = const FakeViewPadding(bottom: 300);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byType(TextField));
    expect(controller.text, 'Retained input');
    expect(
      tester.getRect(find.byType(TextField)).bottom,
      lessThanOrEqualTo(544),
    );
    expect(
      tester.getRect(find.byType(DefaultButton)).bottom,
      lessThanOrEqualTo(544),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('reduced motion produces immediate selected-state transitions', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        Builder(
          builder: (context) {
            return AnimatedContainer(
              duration: SokounMotion.duration(context),
              color: Colors.teal,
            );
          },
        ),
        reducedMotion: true,
      ),
    );
    expect(
      tester.widget<AnimatedContainer>(find.byType(AnimatedContainer)).duration,
      Duration.zero,
    );
  });
}

Widget _app(Widget home, {double scale = 1, bool reducedMotion = false}) =>
    ScreenUtilInit(
      designSize: const Size(360, 690),
      enableScaleWH: () => false,
      enableScaleText: () => false,
      fontSizeResolver: (size, _) => size.toDouble(),
      builder: (context, _) => MaterialApp(
        theme: SokounTheme.light,
        home: Builder(
          builder: (context) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: reducedMotion,
            ),
            child: home,
          ),
        ),
      ),
    );
