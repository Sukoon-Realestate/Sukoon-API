import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/saved_folders_screen.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() => registerFeatureTestDependencies(FeatureTestRepository()));
  for (final reduced in [false, true]) {
    testWidgets(
      'folder save and rename survive closing rebuild reduced=$reduced',
      (tester) async {
        await tester.pumpWidget(
          featureTestHost(const SavedFoldersScreen(), reducedMotion: reduced),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.personalNewFolder));
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'Folder lifecycle');
        await tester.tap(find.text(LocaleKeys.personalSave));
        await tester.pump();
        // The result future has completed, but the reverse transition may still
        // have a mounted TextField. Rebuild it as hot reload / theme changes do.
        tester.binding.buildOwner!.reassemble(tester.binding.rootElement!);
        await tester.pump();
        expect(tester.takeException(), isNull);
        await tester.pumpAndSettle();
        expect(find.text('Folder lifecycle'), findsOneWidget);
        await tester.tap(find.text('Folder lifecycle'));
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.personalEdit));
        await tester.pumpAndSettle();
        expect(
          tester.widget<TextField>(find.byType(TextField)).controller!.text,
          'Folder lifecycle',
        );
        await tester.enterText(find.byType(TextField), 'Renamed folder');
        await tester.tap(find.text(LocaleKeys.personalSave));
        await tester.pump();
        tester.binding.buildOwner!.reassemble(tester.binding.rootElement!);
        await tester.pumpAndSettle();
        expect(find.text('Renamed folder'), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets('folder dismissal survives closing rebuild reduced=$reduced', (
      tester,
    ) async {
      await tester.pumpWidget(
        featureTestHost(const SavedFoldersScreen(), reducedMotion: reduced),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.personalNewFolder));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), 'Discarded draft');
      Go.back();
      await tester.pump();
      tester.binding.buildOwner!.reassemble(tester.binding.rootElement!);
      await tester.pumpAndSettle();
      expect(find.text('Discarded draft'), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.tap(find.text(LocaleKeys.personalNewFolder));
      await tester.pumpAndSettle();
      expect(
        tester.widget<TextField>(find.byType(TextField)).controller!.text,
        isEmpty,
      );
      Go.back();
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
