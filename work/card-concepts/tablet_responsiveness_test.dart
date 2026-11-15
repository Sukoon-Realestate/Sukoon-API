import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import 'package:melos_core/core/widgets/default_bottom_sheet.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/models/home_navigation_destination.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_navigation_rail.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() => registerFeatureTestDependencies(FeatureTestRepository()));
  for (final locale in ['ar', 'en']) {
    for (final scale in [1.0, 2.0]) {
      for (final size in [
        const Size(390, 844),
        const Size(768, 1024),
        const Size(1366, 768),
      ]) {
        testWidgets('profile reflows $locale $scale $size', (tester) async {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          final boundary = GlobalKey();
          Widget page() => featureTestHost(
            RepaintBoundary(
              key: boundary,
              child: ProfileScaffold(
                workspace: AppWorkspace.individual,
                body: ProfileContentView(
                  workspace: AppWorkspace.individual,
                  header: const Text('Account identity'),
                  accountDetails: const ProfileAccountDetailsContent.initial(),
                  isVerified: true,
                  activity: const SizedBox(
                    height: 100,
                    child: Text('Activity'),
                  ),
                  additionalSections: const [Text('Additional tools')],
                ),
              ),
            ),
            locale: locale,
            scale: scale,
            reducedMotion: scale == 2,
          );
          await tester.pumpWidget(page());
          await tester.pumpAndSettle();
          final verification = tester.getRect(
            find.byType(ProfileVerificationTile),
          );
          final activity = tester.getRect(find.text('Activity'));
          final twoColumns = size.width >= 768 && scale == 1;
          if (twoColumns) {
            expect(activity.top, closeTo(verification.top, 1));
            expect((activity.left - verification.left).abs(), greaterThan(250));
          } else {
            expect(activity.top, greaterThanOrEqualTo(verification.bottom));
          }
          expect(tester.takeException(), isNull);
          if (locale == 'ar' && scale == 1 && size.width == 1366) {
            await tester.runAsync(() async {
              final render =
                  boundary.currentContext!.findRenderObject()!
                      as RenderRepaintBoundary;
              final image = await render.toImage(pixelRatio: 1);
              final bytes = await image.toByteData(
                format: ui.ImageByteFormat.png,
              );
              await File(
                '/tmp/tablet-profile-ar.png',
              ).writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
        });
      }
      testWidgets('local toolbar and form width $locale $scale', (
        tester,
      ) async {
        tester.view.physicalSize = const Size(1366, 768);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final controller = TextEditingController(text: 'Retained draft');
        addTearDown(controller.dispose);
        await tester.pumpWidget(
          featureTestHost(
            Center(
              child: SizedBox(
                width: 496,
                child: AppScaffold(
                  contentWidth: SokounContentWidth.form,
                  title: 'Account settings and preferences',
                  showBackButton: false,
                  actions: [
                    for (final icon in [Icons.help, Icons.settings, Icons.info])
                      IconButton(onPressed: () {}, icon: Icon(icon)),
                  ],
                  body: ListView(children: [TextField(controller: controller)]),
                ),
              ),
            ),
            locale: locale,
            scale: scale,
          ),
        );
        await tester.pumpAndSettle();
        final bar = tester.getRect(find.byType(GlassAppBar));
        final field = tester.getRect(find.byType(TextField));
        expect(bar.left, closeTo(field.left, 1));
        expect(bar.right, closeTo(field.right, 1));
        for (final button in tester.widgetList<IconButton>(
          find.byType(IconButton),
        )) {
          final rect = tester.getRect(find.byWidget(button));
          expect(rect.left, greaterThanOrEqualTo(bar.left));
          expect(rect.right, lessThanOrEqualTo(bar.right));
        }
        await tester.enterText(find.byType(TextField), 'Edited draft');
        tester.view.physicalSize = const Size(768, 1024);
        await tester.pumpAndSettle();
        expect(controller.text, 'Edited draft');
        expect(tester.takeException(), isNull);
      });
      testWidgets('rail enlarged labels remain reachable $locale $scale', (
        tester,
      ) async {
        tester.view.physicalSize = const Size(1024, 600);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        int selected = -1;
        late bool splitRail;
        await tester.pumpWidget(
          featureTestHost(
            Scaffold(
              body: Builder(
                builder: (context) {
                  splitRail = SokounLayout.usesNavigationRail(context, 600);
                  return SizedBox(
                    width: SokounLayout.navigationWidth(context),
                    child: HomeNavigationRail(
                      currentIndex: 0,
                      destinations: [
                        for (var i = 0; i < 5; i++)
                          HomeNavigationDestination(
                            icon: Icons.home_outlined,
                            selectedIcon: Icons.home,
                            label: locale == 'ar'
                                ? 'السكن الخاص $i'
                                : 'My housing $i',
                          ),
                      ],
                      onDestinationSelected: (index) => selected = index,
                    ),
                  );
                },
              ),
            ),
            locale: locale,
            scale: scale,
          ),
        );
        await tester.pumpAndSettle();
        expect(splitRail, scale == 1);
        final last = find.text(
          locale == 'ar' ? 'السكن الخاص 4' : 'My housing 4',
        );
        await tester.ensureVisible(last);
        await tester.pumpAndSettle();
        await tester.tap(last);
        await tester.pumpAndSettle();
        expect(selected, 4);
        expect(tester.takeException(), isNull);
      });
    }
  }
  for (final workspace in AppWorkspace.values) {
    for (final scale in [1.0, 2.0]) {
      testWidgets('tablet settings $workspace text=$scale', (tester) async {
        tester.view.physicalSize = const Size(1024, 1366);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await tester.pumpWidget(
          featureTestHost(
            ProfileSettingsScreen(workspace: workspace),
            scale: scale,
          ),
        );
        await tester.pumpAndSettle();
        final sections = find.byType(ProfileMenuSection);
        expect(sections, findsAtLeastNWidgets(2));
        final first = tester.getRect(sections.at(0));
        final second = tester.getRect(sections.at(1));
        if (scale == 1) {
          expect(first.top, closeTo(second.top, 1));
        } else {
          expect(second.top, greaterThan(first.top));
        }
        final logout = find.byType(ProfileLogoutButton);
        await tester.scrollUntilVisible(
          logout,
          400,
          scrollable: find
              .descendant(
                of: find.byType(ListView).first,
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await tester.pumpAndSettle();
        expect(logout.hitTestable(), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }
  testWidgets('tablet sheet width and keyboard ownership', (tester) async {
    tester.view.physicalSize = const Size(1366, 768);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    double? inset;
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(viewInsets: const EdgeInsets.only(bottom: 240)),
          child: child!,
        ),
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showDefaultBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                builder: (context) {
                  inset = MediaQuery.viewInsetsOf(context).bottom;
                  return const SizedBox(
                    key: ValueKey('sheet'),
                    width: double.infinity,
                    height: 120,
                    child: Text('Choices'),
                  );
                },
              ),
              child: const Text('Open'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    final bounds = tester.getRect(find.byKey(const ValueKey('sheet')));
    expect(bounds.width, 640);
    expect(bounds.center.dx, 683);
    expect(bounds.bottom, lessThanOrEqualTo(528));
    expect(inset, 0);
    expect(tester.takeException(), isNull);
  });
}
