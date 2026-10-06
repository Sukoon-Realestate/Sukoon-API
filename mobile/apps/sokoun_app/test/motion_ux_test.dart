import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:toastification/toastification.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_review_action.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_review_sheet.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_review_section.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/tenant_recent_searches_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/filter_price_range_section.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/filter_apply_bar.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/property_description.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search/recent_searches_section.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search/tenant_search_field.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_content_transition.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_feedback.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_chip.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart'
    show OwnerAvailabilityTimeChip, OwnerAvailabilitySlotState;
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/filter_chip_wrap.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => toastification.managers.clear());
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
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

  test(
    'price ranges support open bounds and reject reversed or invalid amounts',
    () {
      const initial = PropertySearchFilters.initial();
      expect(initial.hasValidPriceRange, isTrue);
      expect(
        initial.copyWith(priceMin: '0', priceMax: '0').hasValidPriceRange,
        isTrue,
      );
      expect(initial.copyWith(priceMin: '5000').hasValidPriceRange, isTrue);
      expect(initial.copyWith(priceMax: '5000').hasValidPriceRange, isTrue);
      expect(
        initial.copyWith(priceMin: '9000', priceMax: '1000').hasValidPriceRange,
        isFalse,
      );
      expect(initial.copyWith(priceMin: '-1').hasValidPriceRange, isFalse);
      expect(initial.copyWith(priceMax: 'NaN').hasValidPriceRange, isFalse);
    },
  );

  test(
    'numeric input accepts Arabic and Persian digits and preserves selection',
    () {
      const formatter = LocalizedDigitsFormatter();
      final result = formatter.formatEditUpdate(
        TextEditingValue.empty,
        const TextEditingValue(
          text: '١٢۳۴',
          selection: TextSelection.collapsed(offset: 4),
        ),
      );
      expect(result.text, '1234');
      expect(result.selection.baseOffset, 4);
    },
  );

  testWidgets('entrance animates once and keeps child state on rebuild', (
    tester,
  ) async {
    final controller = TextEditingController();
    addTearDown(controller.dispose);
    await tester.pumpWidget(
      _app(SokounReveal(child: TextField(controller: controller))),
    );
    await tester.pump();
    final fade = find.descendant(
      of: find.byType(SokounReveal),
      matching: find.byType(FadeTransition),
    );
    await tester.pump(const Duration(milliseconds: 100));
    final value = tester.widget<FadeTransition>(fade).opacity.value;
    expect(value, greaterThan(0));
    expect(value, lessThan(1));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Retained');
    final state = tester.state(find.byType(TextField));
    await tester.pumpWidget(
      _app(SokounReveal(child: TextField(controller: controller))),
    );
    await tester.pump();
    expect(tester.state(find.byType(TextField)), same(state));
    expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
    expect(controller.text, 'Retained');
  });

  testWidgets('reduced motion bypasses the entrance, including its stagger', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        const SokounReveal(
          delay: Duration(milliseconds: 160),
          beginScale: .88,
          child: Text('Visible'),
        ),
        reduced: true,
      ),
    );
    await tester.pumpAndSettle();
    final fade = find.descendant(
      of: find.byType(SokounReveal),
      matching: find.byType(FadeTransition),
    );
    expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
    expect(
      tester
          .widget<ScaleTransition>(
            find.descendant(
              of: find.byType(SokounReveal),
              matching: find.byType(ScaleTransition),
            ),
          )
          .scale
          .value,
      1,
    );
  });

  testWidgets(
    'context transitions retain form state and do not replay on rebuild',
    (tester) async {
      final identity = ValueNotifier(0);
      final controller = TextEditingController();
      addTearDown(identity.dispose);
      addTearDown(controller.dispose);
      Widget content() => _app(
        ValueListenableBuilder<int>(
          valueListenable: identity,
          builder: (_, value, _) => SokounContentTransition(
            identity: value,
            child: TextField(controller: controller),
          ),
        ),
      );
      await tester.pumpWidget(content());
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), 'Retained address');
      final fieldState = tester.state(find.byType(TextField));
      identity.value = 1;
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 80));
      final fade = find.descendant(
        of: find.byType(SokounContentTransition),
        matching: find.byType(FadeTransition),
      );
      expect(
        tester.widget<FadeTransition>(fade).opacity.value,
        inExclusiveRange(.65, 1),
      );
      expect(tester.state(find.byType(TextField)), same(fieldState));
      expect(find.text('Retained address'), findsOneWidget);
      await tester.pumpAndSettle();
      await tester.pumpWidget(content());
      expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
      expect(controller.text, 'Retained address');
    },
  );

  for (final accessible in [false, true]) {
    testWidgets(
      'changing the motion preference settles active transitions ($accessible)',
      (tester) async {
        final identity = ValueNotifier(0);
        addTearDown(identity.dispose);
        Widget content({bool reduced = false}) => _app(
          ValueListenableBuilder<int>(
            valueListenable: identity,
            builder: (_, value, _) => SokounContentTransition(
              identity: value,
              child: const Text('Current content'),
            ),
          ),
          reduced: reduced && !accessible,
          accessible: reduced && accessible,
        );
        await tester.pumpWidget(content());
        await tester.pumpAndSettle();
        identity.value = 1;
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 40));
        await tester.pumpWidget(content(reduced: true));
        final fade = find.descendant(
          of: find.byType(SokounContentTransition),
          matching: find.byType(FadeTransition),
        );
        expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
        identity.value = 2;
        await tester.pump();
        expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
      },
    );
  }

  testWidgets(
    'selection feedback pulses once then returns to its original size',
    (tester) async {
      final selected = ValueNotifier(false);
      addTearDown(selected.dispose);
      Widget content({bool reduced = false}) => _app(
        ValueListenableBuilder<bool>(
          valueListenable: selected,
          builder: (_, value, _) => SokounSelectionFeedback(
            selected: value,
            child: const Icon(Icons.bookmark_rounded),
          ),
        ),
        reduced: reduced,
      );
      await tester.pumpWidget(content());
      await tester.pumpAndSettle();
      final transform = find.descendant(
        of: find.byType(SokounSelectionFeedback),
        matching: find.byType(Transform),
      );
      double scale() =>
          tester.widget<Transform>(transform).transform.storage[0];
      expect(scale(), 1);
      selected.value = true;
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 60));
      expect(scale(), inExclusiveRange(1, 1.09));
      await tester.pumpAndSettle();
      expect(scale(), closeTo(1, .0001));
      await tester.pumpWidget(content(reduced: true));
      selected.value = false;
      await tester.pump();
      expect(scale(), 1);
    },
  );

  testWidgets(
    'inactive content settles without replaying when it becomes visible',
    (tester) async {
      Widget content(int identity, bool active) => _app(
        TickerMode(
          enabled: active,
          child: SokounContentTransition(
            identity: identity,
            child: const Text('Kept alive'),
          ),
        ),
      );
      await tester.pumpWidget(content(0, true));
      await tester.pumpAndSettle();
      await tester.pumpWidget(content(1, true));
      await tester.pump(const Duration(milliseconds: 40));
      await tester.pumpWidget(content(1, false));
      await tester.pumpWidget(content(2, false));
      await tester.pumpWidget(content(2, true));
      final fade = find.descendant(
        of: find.byType(SokounContentTransition),
        matching: find.byType(FadeTransition),
      );
      expect(tester.widget<FadeTransition>(fade).opacity.value, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'selection chips expose their selected state to assistive technology',
    (tester) async {
      final semantics = tester.ensureSemantics();
      try {
        final selected = ValueNotifier(false);
        addTearDown(selected.dispose);
        await tester.pumpWidget(
          _app(
            ValueListenableBuilder<bool>(
              valueListenable: selected,
              builder: (_, value, _) => SokounSelectionChip(
                label: 'Elevator',
                selected: value,
                onPressed: () => selected.value = !value,
              ),
            ),
            reduced: true,
          ),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text('Elevator'));
        await tester.pumpAndSettle();
        final node = tester.getSemantics(find.byType(SokounSelectionChip));
        expect(
          node.getSemanticsData().flagsCollection.isSelected,
          ui.Tristate.isTrue,
        );
        expect(node.getSemanticsData().flagsCollection.isButton, isTrue);
        expect(node.label, 'Elevator');
      } finally {
        semantics.dispose();
      }
    },
  );

  for (final language in ['ar', 'en']) {
    testWidgets('long descriptions expand and collapse in $language', (
      tester,
    ) async {
      _size(tester, 390);
      final description = List.filled(
        12,
        language == 'ar'
            ? 'شقة مضيئة قريبة من المواصلات والخدمات.'
            : 'A bright apartment near transport and local services.',
      ).join(' ');
      await tester.pumpWidget(
        _app(
          SingleChildScrollView(
            child: PropertyDescription(description: description),
          ),
          language: language,
        ),
      );
      await tester.pumpAndSettle();
      final collapsed = tester.getSize(find.byType(AnimatedSize)).height;
      await tester.tap(find.text(LocaleKeys.showMore));
      await tester.pumpAndSettle();
      expect(
        tester.getSize(find.byType(AnimatedSize)).height,
        greaterThan(collapsed),
      );
      await tester.ensureVisible(find.text(LocaleKeys.showLess));
      await tester.tap(find.text(LocaleKeys.showLess));
      await tester.pumpAndSettle();
      expect(
        tester.getSize(find.byType(AnimatedSize)).height,
        closeTo(collapsed, .1),
      );
      expect(tester.takeException(), isNull);
    });

    for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
      for (final scale in [1.0, 1.3, 2.0]) {
        testWidgets('animated controls fit $language $width $scale', (
          tester,
        ) async {
          _size(tester, width);
          final selected = ValueNotifier(false);
          addTearDown(selected.dispose);
          final ownerLabel = language == 'ar'
              ? 'تكييف هواء'
              : 'Air conditioning';
          final filterLabel = language == 'ar'
              ? 'قريب من المواصلات والخدمات الأساسية'
              : 'Close to public transport and essential services';
          await tester.pumpWidget(
            _app(
              _MotionSelectionPreview(
                selected: selected,
                ownerLabel: ownerLabel,
                filterLabel: filterLabel,
              ),
              language: language,
              scale: scale,
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          for (final chip in tester.widgetList<SokounSelectionChip>(
            find.byType(SokounSelectionChip),
          )) {
            expect(
              tester.getSize(find.byWidget(chip)).height,
              greaterThanOrEqualTo(48),
            );
          }
          final capture = scale == 1 && (width == 390 || width == 1024);
          if (capture) {
            await _capture(
              tester,
              'selection-before-$language-${width.toInt()}',
            );
          }
          await tester.tap(find.text(ownerLabel));
          await tester.pump();
          await tester.pump(const Duration(milliseconds: 70));
          expect(tester.takeException(), isNull);
          if (capture) {
            await _capture(
              tester,
              'selection-during-$language-${width.toInt()}',
            );
          }
          await tester.pumpAndSettle();
          expect(selected.value, isTrue);
          if (capture) {
            await _capture(
              tester,
              'selection-after-$language-${width.toInt()}',
            );
          }
          await tester.tap(find.text(filterLabel));
          await tester.pumpAndSettle();
          expect(selected.value, isFalse);
          expect(tester.takeException(), isNull);
        });

        testWidgets(
          'search can clear its query and delete history with Undo in $language $width $scale',
          (tester) async {
            _size(tester, width);
            final controller = TextEditingController(text: 'Maadi');
            final cubit = TenantRecentSearchesCubit();
            addTearDown(controller.dispose);
            addTearDown(cubit.close);
            await cubit.addRecentSearch('Maadi');
            await cubit.addRecentSearch('Zamalek');
            String? changed;
            await tester.pumpWidget(
              _app(
                BlocProvider.value(
                  value: cubit,
                  child: SingleChildScrollView(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          TenantSearchField(
                            controller: controller,
                            onChanged: (value) => changed = value,
                          ),
                          BlocBuilder<
                            TenantRecentSearchesCubit,
                            List<RecentSearchContent>
                          >(
                            builder: (_, searches) => RecentSearchesSection(
                              searches: searches,
                              onSelected: (_) {},
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                language: language,
                scale: scale,
              ),
            );
            await tester.pumpAndSettle();
            if (scale == 1 && (width == 390 || width == 1024)) {
              await _capture(tester, 'search-$language-${width.toInt()}');
            }
            await tester.tap(find.byTooltip(LocaleKeys.clearSearchQuery));
            await tester.pumpAndSettle();
            expect(controller.text, isEmpty);
            expect(changed, '');
            await tester.tap(
              find.byTooltip('${LocaleKeys.removeRecentSearch}: Zamalek'),
            );
            await tester.pump();
            await tester.pump(const Duration(milliseconds: 400));
            expect(cubit.state.single.title, 'Maadi');
            await _waitForUndo(tester);
            await tester.tap(find.text(LocaleKeys.undoAction));
            await tester.pumpAndSettle();
            expect(cubit.state.map((item) => item.title), ['Zamalek', 'Maadi']);
            await tester.tap(find.text(LocaleKeys.clearSearchHistory));
            await tester.pump();
            await tester.pump(const Duration(milliseconds: 400));
            expect(cubit.state, isEmpty);
            await _waitForUndo(tester);
            await tester.tap(find.text(LocaleKeys.undoAction));
            await tester.pumpAndSettle();
            expect(cubit.state.map((item) => item.title), ['Zamalek', 'Maadi']);
            expect(tester.takeException(), isNull);
          },
        );

        testWidgets(
          'review is scrollable and edits the correct section $language $width $scale',
          (tester) async {
            _size(tester, width);
            PropertyReviewAction? result;
            await tester.pumpWidget(
              _app(
                Builder(
                  builder: (context) => TextButton(
                    onPressed: () async {
                      result = await showModalBottomSheet<PropertyReviewAction>(
                        context: context,
                        isScrollControlled: true,
                        useSafeArea: true,
                        showDragHandle: true,
                        constraints: BoxConstraints(
                          maxWidth: 640,
                          maxHeight: MediaQuery.sizeOf(context).height * .9,
                        ),
                        builder: (_) => PropertyReviewSheet(
                          form: _reviewForm(),
                          isEditing: false,
                        ),
                      );
                    },
                    child: const Text('Open review'),
                  ),
                ),
                language: language,
                scale: scale,
              ),
            );
            await tester.pumpAndSettle();
            await tester.tap(find.text('Open review'));
            await tester.pumpAndSettle();
            expect(find.byType(PropertyReviewSheet), findsOneWidget);
            expect(find.byType(PropertyReviewSection), findsNWidgets(4));
            expect(
              find.textContaining(
                language == 'ar' ? '18,000 ج.م' : '18,000 EGP',
              ),
              findsOneWidget,
            );
            if (scale == 1 && (width == 390 || width == 1024)) {
              await _capture(tester, 'review-$language-${width.toInt()}');
            }
            final action = find.descendant(
              of: find.byType(PropertyReviewSection).first,
              matching: find.byType(IconButton),
            );
            await tester.ensureVisible(action);
            await tester.pumpAndSettle();
            await tester.tap(action);
            await tester.pumpAndSettle();
            expect(result, PropertyReviewAction.basics);
            expect(tester.takeException(), isNull);
          },
        );
      }
    }
  }

  testWidgets('price correction swaps bounds and enables applying results', (
    tester,
  ) async {
    _size(tester, 320);
    final minimum = TextEditingController(text: '9000');
    final maximum = TextEditingController(text: '1000');
    final filters = ValueNotifier(
      const PropertySearchFilters.initial().copyWith(
        priceMin: '9000',
        priceMax: '1000',
      ),
    );
    addTearDown(minimum.dispose);
    addTearDown(maximum.dispose);
    addTearDown(filters.dispose);
    int applied = 0;
    await tester.pumpWidget(
      _app(
        ValueListenableBuilder<PropertySearchFilters>(
          valueListenable: filters,
          builder: (_, value, _) => Column(
            children: [
              FilterPriceRangeSection(
                filters: value,
                minPriceController: minimum,
                maxPriceController: maximum,
                onFiltersChanged: (value) => filters.value = value,
              ),
              FilterApplyBar(
                onApplyPressed: value.hasValidPriceRange
                    ? () => applied++
                    : null,
              ),
            ],
          ),
        ),
        scale: 2,
      ),
    );
    await tester.pumpAndSettle();
    expect(
      tester.widget<DefaultButton>(find.byType(DefaultButton)).onTap,
      isNull,
    );
    await tester.tap(find.text(LocaleKeys.swapPriceRange));
    await tester.pumpAndSettle();
    expect(minimum.text, '1000');
    expect(maximum.text, '9000');
    await tester.tap(find.text(LocaleKeys.tenantFilterShowResults));
    expect(applied, 1);
    expect(tester.takeException(), isNull);
  });
}

class _MotionSelectionPreview extends StatelessWidget {
  const _MotionSelectionPreview({
    required this.selected,
    required this.ownerLabel,
    required this.filterLabel,
  });

  final ValueNotifier<bool> selected;
  final String ownerLabel;
  final String filterLabel;

  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.topCenter,
    child: SizedBox(
      width: 520,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: ValueListenableBuilder<bool>(
          valueListenable: selected,
          builder: (_, value, _) => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 20,
            children: [
              Text(LocaleKeys.ownerAddPropertyType),
              Wrap(
                children: [
                  AddPropertyChip(
                    chip: AddPropertyChipContent(
                      label: ownerLabel,
                      isSelected: value,
                    ),
                    onTap: () => selected.value = !value,
                  ),
                ],
              ),
              const Divider(),
              Text(LocaleKeys.tenantFilterShowResults),
              FilterChipWrap(
                options: [
                  TenantFilterOption(value: 'transport', label: filterLabel),
                ],
                selectedValues: value ? {'transport'} : {},
                onSelected: (_) => selected.value = !value,
              ),
              const Divider(),
              Text(LocaleKeys.ownerAvailabilityDescription),
              Row(
                spacing: 12,
                children: [
                  Expanded(
                    child: OwnerAvailabilityTimeChip(
                      label: '09:00 AM',
                      state: value
                          ? OwnerAvailabilitySlotState.available
                          : OwnerAvailabilitySlotState.unspecified,
                      onPressed: () => selected.value = !value,
                    ),
                  ),
                  Expanded(
                    child: OwnerAvailabilityTimeChip(
                      label: '10:00 AM',
                      state: OwnerAvailabilitySlotState.booked,
                      onPressed: () {},
                    ),
                  ),
                ],
              ),
              const Divider(),
              Row(
                children: [
                  Expanded(child: Text(LocaleKeys.favoritesNavigationSaved)),
                  IconButton(
                    onPressed: () => selected.value = !value,
                    icon: SokounSelectionFeedback(
                      selected: value,
                      child: Icon(
                        value
                            ? Icons.bookmark_rounded
                            : Icons.bookmark_border_rounded,
                        color: AppColors.sokoonTeal,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

OwnerAddPropertyFormState _reviewForm() =>
    OwnerAddPropertyFormState.initial().copyWith(
      title: 'Bright apartment / شقة بإضاءة طبيعية',
      propertyType: 'Apartment',
      governorate: 'Cairo',
      district: 'Maadi',
      street: 'Quiet residential street',
      photoDrafts: [
        for (var i = 0; i < 10; i++)
          OwnerPropertyPhotoDraft(
            existingId: 'photo-$i',
            existingUrl: 'https://example.com/photo-$i.jpg',
          ),
      ],
      bedrooms: '2',
      bathrooms: '1',
      space: '120',
      floor: '3',
      rentalDuration: '12',
      rentalUnit: 'Month',
      monthlyPrice: '18000',
      description: List.filled(
        6,
        'Near public transport and services.',
      ).join(' '),
      amenities: {'Wi-Fi', 'Elevator'},
      suitableFor: 'Families',
    );

void _size(WidgetTester tester, double width) {
  tester.view.physicalSize = Size(width, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Widget _app(
  Widget child, {
  String language = 'en',
  bool reduced = false,
  bool accessible = false,
  double scale = 1,
}) => EasyLocalization(
  supportedLocales: const [Locale('en'), Locale('ar')],
  startLocale: Locale(language),
  saveLocale: false,
  path: 'unused',
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    enableScaleWH: () => false,
    enableScaleText: () => false,
    fontSizeResolver: (size, _) => size.toDouble(),
    builder: (context, _) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      theme: SokounTheme.light,
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      builder: (context, navigator) => MediaQuery(
        data: MediaQuery.of(context).copyWith(
          disableAnimations: reduced,
          accessibleNavigation: accessible,
          textScaler: TextScaler.linear(scale),
        ),
        child: RepaintBoundary(child: navigator!),
      ),
      home: AppScaffold(showBackButton: false, body: SafeArea(child: child)),
    ),
  ),
);

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}

Future<void> _capture(WidgetTester tester, String name) async {
  const output = String.fromEnvironment('MOTION_REVIEW_DIR');
  if (output.isEmpty) return;
  final RenderRepaintBoundary boundary = tester.renderObject(
    find.byType(RepaintBoundary).first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await Directory(output).create(recursive: true);
    await File('$output/$name.png').writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

Future<void> _waitForUndo(WidgetTester tester) async {
  // Persistence and the toast overlay each complete on a later frame.
  for (
    var frame = 0;
    frame < 10 && find.text(LocaleKeys.undoAction).evaluate().isEmpty;
    frame++
  ) {
    await tester.pump(const Duration(milliseconds: 50));
  }
  expect(find.text(LocaleKeys.undoAction), findsOneWidget);
  await tester.pump(const Duration(milliseconds: 250));
  await tester.pump();
  expect(find.text(LocaleKeys.undoAction).hitTestable(), findsOneWidget);
}
