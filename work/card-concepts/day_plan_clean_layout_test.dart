import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/shared/visit_decisions/presentation/cubits/viewing_day_plan_cubit.dart';
import 'package:sokoun_app/features/shared/visit_decisions/presentation/widgets/viewing_day_plan_content.dart';
import 'package:sokoun_app/features/shared/visit_decisions/data/models/viewing_day_plan.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    final repository = FeatureTestRepository();
    repository.handler = (_) async => const FeatureTestReply(data: {
      'protocol': 1, 'timezone': 'Africa/Cairo', 'day': '2026-11-15', 'revision': 'fixture', 'visits': [],
    });
    await registerFeatureTestDependencies(repository);
  });
  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0]) {
      for (final dark in [false, true]) {
        for (final scale in [1.0, 2.0]) {
          testWidgets('day plan $locale width=$width dark=$dark scale=$scale', (tester) async {
            tester.view.physicalSize = Size(width, 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final cubit = ViewingDayPlanCubit('individual', day: DateTime(2026, 11, 15));
            addTearDown(cubit.close);
            await cubit.load();
            final boundary = GlobalKey();
            await tester.pumpWidget(featureTestHost(RepaintBoundary(key: boundary,
              child: Builder(builder: (_) => AppScaffold(title: LocaleKeys.dayPlanTitle,
                body: BlocBuilder<ViewingDayPlanCubit, AsyncState<ViewingDayState>>(
                  bloc: cubit, builder: (_, state) => ViewingDayPlanContent(cubit: cubit, state: state),
                ),
              )),
            ), locale: locale, dark: dark, scale: scale));
            await tester.pumpAndSettle();
            expect(find.byType(DropdownButtonFormField<int>), findsNWidgets(2));
            expect(find.byType(DropdownButtonFormField<DayTravelMode>), findsOneWidget);
            expect(tester.takeException(), isNull);
            if (locale == 'ar' && width == 390 && !dark && scale == 1) {
              await tester.runAsync(() async {
                final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                final image = await render.toImage(pixelRatio: 2);
                final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                await File('/tmp/day-plan-clean-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            final control = find.byType(DropdownButtonFormField<int>).first;
            await tester.ensureVisible(control);
            await tester.pumpAndSettle();
            await tester.tap(control);
            await tester.pumpAndSettle();
            await tester.tap(find.text('45 ${LocaleKeys.dayPlanMinutes}').last);
            await tester.pumpAndSettle();
            expect(cubit.data.query.viewingMinutes, 45);
            expect(cubit.data.plan, isNull);
            expect(tester.takeException(), isNull);
          });
        }
      }
    }
  }
}
