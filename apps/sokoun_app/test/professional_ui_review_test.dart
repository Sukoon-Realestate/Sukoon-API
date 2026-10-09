import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_property_draft.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_upload_progress.dart';
import 'package:sokoun_app/features/owner/home/data/owner_draft_data.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/owner_draft_cubit.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/owner_draft_status.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/owner_upload_progress_panel.dart';
import 'package:sokoun_app/features/shared/recovery/presentation/widgets/draft_feedback.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'helpers/feature_tools_test_dependencies.dart';

/// Export representative renderings with PROFESSIONAL_UI_REVIEW_DIR.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('PROFESSIONAL_UI_REVIEW_DIR');
  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    await registerFeatureTestDependencies(FeatureTestRepository());
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold', 'Black']) {
      fonts.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await fonts.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });

  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          testWidgets('recovery UI $locale $dark $width scale $scale', (
            tester,
          ) async {
            tester.view.physicalSize = Size(width, width >= 600 ? 900 : 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final photos = [
              const OwnerPropertyPhotoDraft(
                draftKey: 'one',
                name: 'Living room / غرفة المعيشة',
              ),
              const OwnerPropertyPhotoDraft(
                draftKey: 'two',
                name: 'Bedroom / غرفة النوم',
              ),
              const OwnerPropertyPhotoDraft(
                draftKey: 'three',
                name: 'Kitchen / المطبخ',
              ),
            ];
            final uploads = {
              photos[0].reference: PropertyUploadProgress(
                reference: photos[0].reference,
                status: PropertyUploadStatus.confirmed,
                imageId: 'image-1',
              ),
              photos[1].reference: PropertyUploadProgress(
                reference: photos[1].reference,
                status: PropertyUploadStatus.sending,
                sent: 300,
                total: 1000,
              ),
              photos[2].reference: PropertyUploadProgress(
                reference: photos[2].reference,
                status: PropertyUploadStatus.failed,
              ),
            };
            final form = ValueNotifier(
              OwnerAddPropertyFormState.initial().copyWith(photoDrafts: photos),
            );
            final owner = OwnerDraftCubit(
              store: _UiDraftStore(
                OwnerPropertyDraft(
                  form: form.value,
                  hasMissingFiles: true,
                  needsPrivateDocument: true,
                  unknownMutation: true,
                  localSaveFailed: true,
                  uploads: uploads,
                ),
              ),
            );
            await owner.load();
            final panels = <String, Widget>{
              'draft_status': Column(
                children: [
                  OwnerDraftStatus(
                    cubit: owner,
                    form: form,
                    retry: () async {},
                  ),
                  const Expanded(child: SizedBox.shrink()),
                ],
              ),
              'upload_progress': SingleChildScrollView(
                child: OwnerUploadProgressPanel(
                  uploads: uploads,
                  photos: photos,
                ),
              ),
              'visit_review': const VisitRatingSheet(
                propertyTitle: 'Apartment in Maadi / شقة في المعادي',
                visitId: 'visit-1',
              ),
            };
            for (final entry in panels.entries) {
              final boundary = GlobalKey();
              await tester.pumpWidget(
                KeyedSubtree(
                  key: ValueKey('$locale-$dark-$width-$scale-${entry.key}'),
                  child: featureTestHost(
                    RepaintBoundary(
                      key: boundary,
                      child: AppScaffold(
                        title: LocaleKeys.freeResumeDraft,
                        body: entry.value,
                      ),
                    ),
                    locale: locale,
                    dark: dark,
                    scale: scale,
                  ),
                ),
              );
              await tester.pumpAndSettle();
              if (entry.key == 'upload_progress') {
                await tester.tap(find.byType(ExpansionTile));
                await tester.pumpAndSettle();
              }
              expect(
                tester.takeException(),
                isNull,
                reason: '${entry.key} $locale/$width/$scale',
              );
              if (output.isNotEmpty &&
                  (width == 320 || width == 1024) &&
                  (scale == 1 || scale == 2)) {
                final render =
                    boundary.currentContext!.findRenderObject()!
                        as RenderRepaintBoundary;
                await tester.runAsync(() async {
                  final bitmap = await render.toImage(pixelRatio: 1);
                  final bytes = await bitmap.toByteData(
                    format: ui.ImageByteFormat.png,
                  );
                  bitmap.dispose();
                  await Directory(output).create(recursive: true);
                  await File(
                    '$output/${entry.key}_${locale}_${dark ? 'dark' : 'light'}_${width.toInt()}_$scale.png',
                  ).writeAsBytes(bytes!.buffer.asUint8List());
                });
              }
              await tester.pumpWidget(const SizedBox.shrink());
              await tester.pump();
            }
            await owner.close();
            form.dispose();
          });
        }
      }
    }
  }

  for (final locale in ['ar', 'en']) {
    testWidgets(
      'draft choice preserves an edited review with a keyboard in $locale',
      (tester) async {
        tester.view.physicalSize = const Size(320, 690);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await tester.pumpWidget(
          featureTestHost(
            const Scaffold(
              body: VisitRatingSheet(
                propertyTitle: 'Apartment',
                visitId: 'visit-1',
              ),
            ),
            locale: locale,
            scale: 2,
          ),
        );
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextFormField), 'Keep this review');
        tester.view.viewInsets = const FakeViewPadding(bottom: 260);
        await tester.pumpAndSettle();
        expect(find.text('Keep this review'), findsOneWidget);
        expect(tester.takeException(), isNull);
        tester.view.viewInsets = FakeViewPadding.zero;
        await tester.pumpAndSettle();
        final context = tester.element(find.byType(VisitRatingSheet));
        final decision = askToRestoreDraft(context);
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.freeResumeDraft).last);
        await tester.pumpAndSettle();
        expect(await decision, isTrue);
        expect(find.text('Keep this review'), findsOneWidget);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pump();
      },
    );
  }
}

class _UiDraftStore implements OwnerDraftStore {
  _UiDraftStore(this.value);
  OwnerPropertyDraft value;
  @override
  Future<OwnerPropertyDraft> read() async => value;
  @override
  Future<OwnerPropertyDraft> write(OwnerPropertyDraft draft) async =>
      value = draft;
  @override
  Future<void> clear() async => value = const OwnerPropertyDraft.initial();
}
