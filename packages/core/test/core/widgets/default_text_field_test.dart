import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

void main() {
  for (final closeOnOutsideTap in [true, false]) {
    testWidgets('outside taps dismiss focus: $closeOnOutsideTap', (
      tester,
    ) async {
      final focus = FocusNode();
      addTearDown(focus.dispose);
      await tester.pumpWidget(
        _app(
          Column(
            children: [
              DefaultTextField(
                focusNode: focus,
                closeWhenTapOutSide: closeOnOutsideTap,
                decoration: const InputDecoration(hintText: 'Search'),
              ),
              TextButton(onPressed: () {}, child: const Text('Outside')),
            ],
          ),
        ),
      );
      await tester.tap(find.byType(TextField));
      await tester.pump();
      expect(focus.hasFocus, isTrue);
      await tester.tap(find.text('Outside'));
      await tester.pump();
      expect(focus.hasFocus, !closeOnOutsideTap);
    });
  }

  testWidgets('initial text survives rebuilds and form reset restores it', (
    tester,
  ) async {
    final form = GlobalKey<FormState>();
    final rebuild = ValueNotifier(0);
    addTearDown(rebuild.dispose);
    await tester.pumpWidget(
      _app(
        Form(
          key: form,
          child: ValueListenableBuilder<int>(
            valueListenable: rebuild,
            builder: (_, value, _) => DefaultTextField.withTitle(
              upperTitle: 'Photo name',
              initialValue: 'Living room',
              title: 'Photo name $value',
            ),
          ),
        ),
      ),
    );
    expect(find.text('Living room'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'Sunny living room');
    rebuild.value++;
    await tester.pump();
    expect(find.text('Sunny living room'), findsOneWidget);
    form.currentState!.reset();
    await tester.pump();
    expect(find.text('Living room'), findsOneWidget);
  });

  testWidgets('disabled date input does not open its picker', (tester) async {
    final enabled = ValueNotifier(false);
    addTearDown(enabled.dispose);
    int picks = 0;
    await tester.pumpWidget(
      _app(
        ValueListenableBuilder<bool>(
          valueListenable: enabled,
          builder: (_, value, _) => DefaultTextField(
            enabled: value,
            readOnly: true,
            onTap: () => picks++,
            decoration: const InputDecoration(labelText: 'Start date'),
          ),
        ),
      ),
    );
    await tester.tap(find.byType(DefaultTextField));
    await tester.pump();
    expect(picks, 0);
    enabled.value = true;
    await tester.pump();
    await tester.tap(find.byType(DefaultTextField));
    await tester.pump();
    expect(picks, 1);
  });

  testWidgets(
    'unbounded multiline text grows and submits without losing focus',
    (tester) async {
      final focus = FocusNode();
      final controller = TextEditingController();
      addTearDown(focus.dispose);
      addTearDown(controller.dispose);
      int submissions = 0;
      await tester.pumpWidget(
        _app(
          SingleChildScrollView(
            child: DefaultTextField(
              controller: controller,
              focusNode: focus,
              inputType: TextInputType.multiline,
              minLines: 4,
              maxLines: null,
              action: TextInputAction.send,
              onEditingComplete: () => submissions++,
            ),
          ),
        ),
      );
      final originalHeight = tester
          .getSize(find.byType(DefaultTextField))
          .height;
      final text = List.generate(12, (index) => 'Line $index').join('\n');
      await tester.enterText(find.byType(TextField), text);
      await tester.pump();
      expect(controller.text, text);
      expect(
        tester.getSize(find.byType(DefaultTextField)).height,
        greaterThan(originalHeight),
      );
      await tester.testTextInput.receiveAction(TextInputAction.send);
      await tester.pump();
      expect(submissions, 1);
      expect(focus.hasFocus, isTrue);
      expect(tester.takeException(), isNull);
    },
  );
}

Widget _app(Widget child) => ScreenUtilInit(
  designSize: const Size(360, 690),
  enableScaleWH: () => false,
  enableScaleText: () => false,
  builder: (_, _) => MaterialApp(home: Scaffold(body: child)),
);
