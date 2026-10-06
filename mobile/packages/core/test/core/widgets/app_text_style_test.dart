import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

void main() {
  testWidgets('legacy labels retain inherited size and regular weight', (
    tester,
  ) async {
    await tester.pumpWidget(_app(const AppText('Label')));
    final text = tester.widget<Text>(find.text('Label'));
    expect(text.style!.fontSize, isNull);
    expect(text.style!.fontWeight, FontWeight.normal);
    expect(text.style!.height, isNull);
    expect(text.style!.fontFamily, ConstantManager.fontFamily);
  });

  testWidgets('manager style keeps its weight, size and line height', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(const AppText('Label', style: AppTextStyles.extraBold20)),
    );
    final text = tester.widget<Text>(find.text('Label'));
    expect(text.style, AppTextStyles.extraBold20);
  });

  testWidgets('explicit overrides take precedence, including regular weight', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        const AppText(
          'Label',
          style: AppTextStyles.extraBold20,
          fontWeight: FontWeight.normal,
          fontSize: 17,
          color: Colors.red,
          height: 1.7,
          decoration: TextDecoration.underline,
        ),
      ),
    );
    final style = tester.widget<Text>(find.text('Label')).style!;
    expect(style.fontWeight, FontWeight.normal);
    expect(style.fontSize, 17);
    expect(style.color, Colors.red);
    expect(style.height, 1.7);
    expect(style.decoration, TextDecoration.underline);
    expect(style.fontFamily, AppTextStyles.base.fontFamily);
  });

  testWidgets('icon labels honor styles and retain the legacy fallback size', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        const Column(
          children: [
            AppText.withIcon(
              icon: Icon(Icons.home),
              text: 'Styled',
              style: AppTextStyles.bold12,
            ),
            AppText.withIcon(icon: Icon(Icons.home), text: 'Legacy'),
          ],
        ),
      ),
    );
    expect(
      tester.widget<Text>(find.text('Styled')).style,
      AppTextStyles.bold12,
    );
    expect(
      tester.widget<Text>(find.text('Legacy')).style!.fontSize,
      FontSize.s16,
    );
  });

  testWidgets('weight-only styles inherit size and system text scaling', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        const MediaQuery(
          data: MediaQueryData(textScaler: TextScaler.linear(2)),
          child: DefaultTextStyle(
            style: TextStyle(fontSize: 22, height: 1.7),
            child: AppText('Label', style: AppTextStyles.bold),
          ),
        ),
      ),
    );
    final richText = tester.widget<RichText>(
      find.descendant(
        of: find.byType(AppText),
        matching: find.byType(RichText),
      ),
    );
    expect(richText.text.style!.fontSize, 22);
    expect(richText.text.style!.height, 1.7);
    expect(richText.text.style!.fontWeight, FontWeight.bold);
    expect(richText.textScaler.scale(22), 44);
  });

  testWidgets('both shared button labels use the supplied typography', (
    tester,
  ) async {
    final style = AppTextStyles.extraBold20.copyWith(color: Colors.red);
    await tester.pumpWidget(
      _app(
        Column(
          children: [
            DefaultButton(title: 'Continue', textStyle: style, onTap: () {}),
            AppLoadingButton(
              title: 'Submit',
              textStyle: style,
              asyncCall: (_) async {},
            ),
            DefaultButton(title: 'Legacy', onTap: () {}),
          ],
        ),
      ),
    );
    for (final label in ['Continue', 'Submit']) {
      expect(tester.widget<Text>(find.text(label)).style, style);
    }
    final legacy = tester.widget<Text>(find.text('Legacy')).style!;
    expect(legacy.fontSize, FontSize.s13);
    expect(legacy.fontWeight, FontWeightManager.medium);
    expect(legacy.color, AppColors.buttonText);
  });
}

Widget _app(Widget child) => ScreenUtilInit(
  designSize: const Size(360, 690),
  enableScaleWH: () => false,
  enableScaleText: () => false,
  builder: (_, _) => MaterialApp(home: Scaffold(body: child)),
);
