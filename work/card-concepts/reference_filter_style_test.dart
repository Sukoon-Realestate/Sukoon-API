import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/shared_widgets/sokoun_filter_options.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import 'package:sokoun_app/shared_widgets/sokoun_filter_style.dart';
import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0]) {
        for (final scale in [1.0, 2.0]) {
          testWidgets('reference filters $locale dark=$dark width=$width scale=$scale', (tester) async {
            tester.view.physicalSize = Size(width, 600);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            var selected = 0;
            final boundary = GlobalKey();
            final labels = locale == 'ar' ? ['الكل', 'مقبولة', 'بانتظار', 'مرفوضة'] : ['All', 'Accepted', 'Pending', 'Rejected'];
            await tester.pumpWidget(featureTestHost(Scaffold(body: Align(alignment: Alignment.topCenter,
              child: RepaintBoundary(key: boundary, child: Material(color: dark ? SokounPalette.dark.canvas : SokounPalette.light.canvas,
                child: Padding(padding: const EdgeInsets.all(20), child: StatefulBuilder(builder: (context, setState) => Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SokounFilterOptions(labels: labels, selectedIndex: selected, onSelected: (index) => setState(() => selected = index)),
                    const SizedBox(height: 20),
                    Wrap(spacing: 8, children: [
                      ChoiceChip(label: const Text('Apartment'), selected: selected == 0, onSelected: (_) => setState(() => selected = 0)),
                      FilterChip(label: const Text('Room'), selected: selected == 1, onSelected: (_) => setState(() => selected = 1)),
                    ]),
                  ],
                ))),
              )),
            )), locale: locale, dark: dark, scale: scale, reducedMotion: false));
            await tester.pumpAndSettle();
            final context = tester.element(find.byType(SokounFilterOptions));
            final palette = SokounPalette.of(context);
            final on = tester.widget<OutlinedButton>(find.widgetWithText(OutlinedButton, labels[0]));
            final off = tester.widget<OutlinedButton>(find.widgetWithText(OutlinedButton, labels[1]));
            expect(on.style!.backgroundColor!.resolve({}), palette.chip);
            expect(off.style!.backgroundColor!.resolve({})!.a, 0);
            expect(on.style!.side!.resolve({})!.color.a, 0);
            expect(off.style!.side!.resolve({})!.color.a, 0);
            final shape = on.style!.shape!.resolve({})! as RoundedRectangleBorder;
            expect(shape.borderRadius, SokounFilterStyle.radius);
            expect(Theme.of(context).chipTheme.selectedColor, palette.chip);
            expect(Theme.of(context).chipTheme.backgroundColor!.a, 0);
            expect(Theme.of(context).chipTheme.showCheckmark, isFalse);
            for (final pair in [(palette.accent, palette.chip), (palette.muted, palette.canvas), (palette.disabledText, palette.canvas)]) {
              final a = pair.$1.computeLuminance(), b = pair.$2.computeLuminance();
              expect((a > b ? (a + .05) / (b + .05) : (b + .05) / (a + .05)), greaterThanOrEqualTo(4.5));
            }
            for (final chip in find.byType(SokounSelectionChip).evaluate()) {
              final size = tester.getSize(find.byWidget(chip.widget));
              expect(size.height, greaterThanOrEqualTo(48));
            }
            if (locale == 'ar' && !dark && width == 390 && scale == 1) {
              await tester.runAsync(() async {
                final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                final image = await render.toImage(pixelRatio: 2);
                final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                await File('/tmp/reference-filter-style-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            await tester.tap(find.text(labels[2]));
            await tester.pumpAndSettle();
            expect(selected, 2);
            expect(tester.takeException(), isNull);
          });
        }
      }
    }
  }
}
