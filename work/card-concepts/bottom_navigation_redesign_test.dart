import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/main_view/presentation/models/home_navigation_destination.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_navigation_item.dart';
import 'package:sokoun_app/shared_widgets/sokoun_count_badge.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

const destinations = [
  HomeNavigationDestination(icon: Icons.home_outlined, selectedIcon: Icons.home_rounded, label: 'الرئيسية'),
  HomeNavigationDestination(icon: Icons.favorite_border_rounded, selectedIcon: Icons.favorite_rounded, label: 'المحفوظة'),
  HomeNavigationDestination(icon: Icons.chat_bubble_outline_rounded, selectedIcon: Icons.chat_bubble_rounded, label: 'الرسائل', badgeCount: 143),
  HomeNavigationDestination(icon: Icons.calendar_today_outlined, selectedIcon: Icons.calendar_today_rounded, label: 'طلبات الزيارة'),
  HomeNavigationDestination(icon: Icons.person_outline_rounded, selectedIcon: Icons.person_rounded, label: 'حسابي'),
];

void main() {
  for (final dark in [false, true]) {
    for (final direction in TextDirection.values) {
      for (final width in [320.0, 390.0]) {
        for (final reduced in [false, true]) {
          testWidgets('dock dark=$dark $direction width=$width reduced=$reduced', (tester) async {
            tester.view.physicalSize = Size(width, 300);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final selected = ValueNotifier(0);
            addTearDown(selected.dispose);
            final calls = <int>[];
            final boundary = GlobalKey();
            await tester.pumpWidget(ScreenUtilInit(
              designSize: const Size(390, 844),
              enableScaleWH: () => false,
              enableScaleText: () => false,
              builder: (_, _) => MaterialApp(
                theme: dark ? SokounTheme.dark : SokounTheme.light,
                home: RepaintBoundary(key: boundary, child: Scaffold(
                  bottomNavigationBar: MediaQuery(
                    data: MediaQueryData(disableAnimations: reduced, textScaler: TextScaler.linear(reduced ? 2 : 1)),
                    child: Directionality(textDirection: direction,
                      child: ValueListenableBuilder<int>(valueListenable: selected, builder: (_, index, _) => HomeBottomNavigation(
                        destinations: destinations, currentIndex: index,
                        onDestinationSelected: (value) { calls.add(value); selected.value = value; },
                      )),
                    ),
                  ),
                )),
              ),
            ));
            await tester.pumpAndSettle();
            expect(find.text('99+'), findsOneWidget);
            final badge = tester.getRect(find.byType(SokounCountBadge));
            final messages = find.byWidgetPredicate((w) => w is HomeNavigationItem && w.destination.label == 'الرسائل');
            final bounds = tester.getRect(messages);
            expect(badge.left, greaterThanOrEqualTo(bounds.left));
            expect(badge.right, lessThanOrEqualTo(bounds.right));
            expect(badge.top, greaterThanOrEqualTo(bounds.top));
            await tester.ensureVisible(messages);
            await tester.tap(messages);
            await tester.pump(const Duration(milliseconds: 75));
            expect(calls, [2]);
            expect(selected.value, 2);
            expect(tester.takeException(), isNull);
            await tester.pumpAndSettle();
            await tester.tap(messages);
            await tester.pumpAndSettle();
            expect(calls, [2, 2]);
            if (width == 390 && direction == TextDirection.rtl && !reduced) {
              await tester.runAsync(() async {
                final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                final image = await render.toImage(pixelRatio: 2);
                final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                await File('/tmp/bottom-nav-${dark ? "dark" : "light"}.png').writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            expect(tester.takeException(), isNull);
          });
        }
      }
    }
  }
}
