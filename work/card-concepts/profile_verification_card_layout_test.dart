import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final verified in [false, true]) {
        for (final scale in [1.0, 2.0]) {
          for (final width in [320.0, 390.0]) {
            testWidgets('verification $locale dark=$dark verified=$verified scale=$scale width=$width', (tester) async {
              tester.view.physicalSize = Size(width, 600);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final boundary = GlobalKey();
              final label = locale == 'ar' ? (verified ? 'موثّق ✓' : 'غير موثق') : (verified ? 'Verified ✓' : 'Not verified');
              await tester.pumpWidget(featureTestHost(Scaffold(body: Padding(
                padding: const EdgeInsets.all(20),
                child: RepaintBoundary(key: boundary, child: ProfileVerificationTile(
                  workspace: AppWorkspace.individual,
                  isVerified: verified,
                  subtitle: label,
                )),
              )), locale: locale, dark: dark, scale: scale));
              await tester.pumpAndSettle();
              expect(find.byIcon(Icons.verified_rounded), verified ? findsOneWidget : findsNothing);
              expect(find.text(label.replaceFirst(' ✓', '')), findsOneWidget);
              final tile = tester.getRect(find.byType(ProfileVerificationTile));
              expect(tile.left, 20);
              expect(tile.right, width - 20);
              expect(tile.height, greaterThanOrEqualTo(48));
              expect(tester.takeException(), isNull);
              if (locale == 'ar' && verified && scale == 1 && width == 390) {
                await tester.runAsync(() async {
                  final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                  final image = await render.toImage(pixelRatio: 2);
                  final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                  await File('/tmp/profile-verification-${dark ? 'dark' : 'light'}.png').writeAsBytes(bytes!.buffer.asUint8List());
                  image.dispose();
                });
              }
            });
          }
        }
      }
    }
  }
}
