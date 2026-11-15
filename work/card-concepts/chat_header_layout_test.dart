import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chats_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() => registerFeatureTestDependencies(FeatureTestRepository()));
  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0]) {
      for (final scale in [1.0, 2.0]) {
        testWidgets('chat header $locale width=$width scale=$scale', (tester) async {
          tester.view.physicalSize = Size(width, 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          final boundary = GlobalKey();
          await tester.pumpWidget(featureTestHost(RepaintBoundary(key: boundary,
            child: const ChatsScreen(workspace: AppWorkspace.individual)), locale: locale, scale: scale));
          await tester.pumpAndSettle();
          final bell = find.byType(NotificationBellButton);
          expect(bell, findsOneWidget);
          final bar = tester.getRect(find.byType(AppBar));
          for (final action in [bell, find.byTooltip(LocaleKeys.personalReplyReminders), find.byTooltip(LocaleKeys.chatMediaSettings)]) {
            final bounds = tester.getRect(action);
            expect(bounds.top, greaterThanOrEqualTo(bar.top));
            expect(bounds.bottom, lessThanOrEqualTo(bar.bottom + 1));
          }
          expect(tester.takeException(), isNull);
          if (locale == 'ar' && width == 390 && scale == 1) {
            await tester.runAsync(() async {
              final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
              final image = await render.toImage(pixelRatio: 2);
              final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
              await File('/tmp/combined-chat-header-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
          await tester.pumpWidget(const SizedBox.shrink());
          await tester.pumpAndSettle();
        });
      }
    }
  }
}
