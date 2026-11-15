import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/profile/data/models/security_sessions.dart';
import 'package:sokoun_app/features/shared/support/imports.dart';
import 'package:sokoun_app/features/shared/experience/presentation/screens/experience_settings_screen.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    final repository = FeatureTestRepository();
    repository.replies['features/v1/experience/capabilities/'] = const FeatureTestReply(data: {'features': ['discovery']});
    await registerFeatureTestDependencies(repository);
  });
  for (final page in ['preferences', 'sessions', 'feedback', 'password']) {
    for (final locale in ['ar', 'en']) {
      for (final dark in [false, true]) {
        for (final scale in [1.0, 2.0]) {
          for (final width in [320.0, 390.0]) {
            testWidgets('clean $page $locale dark=$dark scale=$scale width=$width', (tester) async {
              tester.view.physicalSize = Size(width, 844);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final write = SecurityRevocationCubit();
              addTearDown(write.close);
              final boundary = GlobalKey();
              await tester.pumpWidget(featureTestHost(RepaintBoundary(
                key: boundary,
                child: Builder(builder: (_) => switch (page) {
                  'preferences' => const ExperienceSettingsScreen(workspace: AppWorkspace.individual),
                  'sessions' => AppScaffold(title: LocaleKeys.securitySessionsTitle, body: SecuritySessionsBody(
                    value: const SecuritySessions(items: [SecuritySession(
                      id: 'session-fixture', current: true, model: 'iPhone 18 Pro', platform: 'iOS', os: '27.0', appVersion: '1.0.0 (7)',
                      lastSeen: '2026-11-15T11:52:00Z', createdAt: '2026-11-14T06:38:00Z',
                    )]), workspace: AppWorkspace.individual, write: write,
                    revoke: () async {}, revokeSession: (_) async {}, revokeOthers: () async {},
                  )),
                  'feedback' => const SupportNewTicketScreen(workspace: AppWorkspace.individual, feedback: true),
                  _ => const ChangePasswordScreen(),
                }),
              ), locale: locale, dark: dark, scale: scale));
              await tester.pumpAndSettle();
              expect(tester.takeException(), isNull);
              if (page == 'feedback') {
                expect(find.byType(ChoiceChip), findsWidgets);
                expect(find.text(LocaleKeys.uiSupportTitle), findsNothing);
              }
              if (page == 'password') {
                expect(find.byType(TextFormField), findsNWidgets(3));
                expect(find.text(LocaleKeys.uiPasswordTitle), findsNothing);
              }
              if (locale == 'ar' && !dark && scale == 1 && width == 390) {
                await tester.runAsync(() async {
                  final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                  final image = await render.toImage(pixelRatio: 2);
                  final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                  await File('/tmp/clean-account-$page.png').writeAsBytes(bytes!.buffer.asUint8List());
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
  }
}
