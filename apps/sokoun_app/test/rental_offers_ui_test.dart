import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_inventory_editor.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_scope_selector.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_review_sheet.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/rental_home/rental_home_section_preview.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import 'helpers/rental_offer_fixtures.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_accommodation_draft_details.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_accommodation_media_section.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_media_review_summary.dart';
import 'package:sokoun_app/features/owner/home/data/owner_accommodation_draft_data.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_basics_page.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_details_section.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_address_section.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_room_fields.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/rental_bed_fields.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_location_model.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Translations translations;
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
    translations = _Translations({
      for (final locale in ['ar', 'en'])
        locale:
            jsonDecode(
                  File(
                    '../../packages/core/assets/translations/$locale.json',
                  ).readAsStringSync(),
                )
                as Map<String, dynamic>,
    });
  });
  setUp(() async {
    await injector.reset();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: _FormRepository()),
    );
  });
  tearDown(() async => injector.reset());

  Future<void> pump(
    WidgetTester tester,
    Widget child, {
    String locale = 'ar',
    double scale = 1,
    double width = 390,
    bool dark = false,
    GlobalKey? capture,
  }) async {
    tester.view.physicalSize = Size(width, 900);
    tester.view.devicePixelRatio = 1;
    await tester.pumpWidget(
      EasyLocalization(
        key: ValueKey('$locale:$dark:$width:$scale'),
        supportedLocales: const [Locale('ar'), Locale('en')],
        path: 'unused',
        assetLoader: translations,
        saveLocale: false,
        startLocale: Locale(locale),
        fallbackLocale: Locale(locale),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          enableScaleWH: () => false,
          enableScaleText: () => false,
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            theme: dark ? SokounTheme.dark : SokounTheme.light,
            locale: context.locale,
            supportedLocales: context.supportedLocales,
            localizationsDelegates: context.localizationDelegates,
            home: Builder(
              builder: (context) => MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(scale),
                  disableAnimations: true,
                ),
                child: RepaintBoundary(
                  key: capture,
                  child: Scaffold(body: SafeArea(child: child)),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'rental editor, selection and review adapt across the required layout matrix',
    (tester) async {
      addTearDown(tester.view.reset);
      final inventory = rentalInventory(
        offers: [bedOffer, independentRooms.last],
      );
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          for (final locale in ['ar', 'en']) {
            for (final dark in [false, true]) {
              for (final subject in ['owner', 'tenant', 'review', 'home']) {
                final capture = GlobalKey();
                final child = subject == 'home'
                    ? SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: RentalHomeSectionPreview(
                          filters: const PropertySearchFilters.initial(
                            rentalScope: 'bed',
                            pricePeriod: 'monthly',
                          ),
                          data: PropertySearchResponseModel(
                            count: 7,
                            next: '?page=2',
                            previous: null,
                            results: [
                              rentalProperty(
                                summary: const RentalListingSummary(
                                  count: 2,
                                  scopes: ['bed'],
                                  labels: ['Bed in Room A'],
                                  price: '1500',
                                  pricePeriod: 'monthly',
                                  priceScope: 'bed',
                                  startingFrom: true,
                                ),
                              ).copyWith(mainImage: '', images: []),
                            ],
                          ),
                        ),
                      )
                    : subject == 'review'
                    ? PropertyReviewSheet(
                        form: rentalForm(inventory),
                        isEditing: true,
                      )
                    : SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: subject == 'owner'
                            ? Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  RentalScopeSelector(
                                    inventory: inventory,
                                    onChanged: (_) {},
                                    onLegacy: () {},
                                  ),
                                  RentalInventoryEditor(
                                    inventory: inventory,
                                    totalRooms: 3,
                                    photos: rentalForm(inventory).photoDrafts,
                                    onChanged: (_) {},
                                  ),
                                ],
                              )
                            : RentalOfferPicker(
                                propertyId: 'property-a',
                                inventory: inventory,
                                selectedId: bedOffer.id,
                                onSelected: (_) {},
                                onConfirmed: (_) {},
                              ),
                      );
                await pump(
                  tester,
                  child,
                  locale: locale,
                  scale: scale,
                  width: width,
                  dark: dark,
                  capture: capture,
                );
                expect(
                  tester.takeException(),
                  isNull,
                  reason: '$subject $width $scale $locale dark=$dark',
                );
                if (subject == 'owner') {
                  expect(find.text(LocaleKeys.rentalLocalOnly), findsWidgets);
                }
                expect(
                  Directionality.of(tester.element(find.byKey(capture))),
                  locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr,
                );
                if (Platform.environment['SOKOUN_CAPTURE_RENTAL_UI'] == '1' &&
                    ((scale == 1 && (width == 390 || width == 1024)) ||
                        (scale == 2 && width == 320)) &&
                    subject != 'review') {
                  await tester.runAsync(() async {
                    final boundary =
                        capture.currentContext!.findRenderObject()!
                            as RenderRepaintBoundary;
                    final image = await boundary.toImage(pixelRatio: 1);
                    final bytes = await image.toByteData(
                      format: ui.ImageByteFormat.png,
                    );
                    final directory = Directory(
                      '${Directory.systemTemp.path}/sokoun-rental-offers-renders',
                    )..createSync(recursive: true);
                    File(
                      '${directory.path}/$subject-${width.toInt()}-$locale-${dark ? 'dark' : 'light'}${scale == 1 ? '' : '-scale$scale'}.png',
                    ).writeAsBytesSync(bytes!.buffer.asUint8List());
                    image.dispose();
                  });
                }
              }
            }
          }
        }
      }
    },
  );
  testWidgets(
    'actual conditional basics forms render all four scopes across the layout matrix',
    (tester) async {
      addTearDown(tester.view.reset);
      var verified = 0;
      for (final offer in [
        wholeOffer,
        independentRooms.first,
        groupOffer,
        bedOffer,
      ]) {
        final inventory = rentalInventory(
          offers: [offer],
          mode: offer.scope == RentalScope.entireProperty ? 'whole' : 'partial',
        );
        for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
          for (final scale in [1.0, 1.3, 2.0]) {
            for (final locale in ['ar', 'en']) {
              for (final dark in [false, true]) {
                final capture = GlobalKey();
                await pump(
                  tester,
                  _ConditionalBasicsHarness(form: rentalForm(inventory)),
                  locale: locale,
                  scale: scale,
                  width: width,
                  dark: dark,
                  capture: capture,
                );
                expect(find.byType(AddPropertyBasicsPage), findsOneWidget);
                expect(find.byType(AddPropertyAddressSection), findsOneWidget);
                expect(
                  find.byType(AddPropertyDetailsSection),
                  offer.scope == RentalScope.entireProperty
                      ? findsOneWidget
                      : findsNothing,
                );
                expect(
                  find.byType(RentalRoomFields),
                  findsNWidgets(offer.roomRefs.length),
                );
                expect(
                  find.byType(RentalBedFields),
                  offer.scope == RentalScope.bed
                      ? findsOneWidget
                      : findsNothing,
                );
                expect(
                  find.text(
                    RentalOfferLabels.formTitle(offer.scope, editing: true),
                  ),
                  findsWidgets,
                );
                expect(
                  tester.takeException(),
                  isNull,
                  reason: '${offer.scope} $width $scale $locale dark=$dark',
                );
                verified++;
                if (Platform.environment['SOKOUN_CAPTURE_RENTAL_UI'] == '1' &&
                    ((scale == 1 && (width == 390 || width == 1024)) ||
                        (scale == 2 && width == 320))) {
                  if (width == 390 && scale == 1) {
                    await captureAccommodationForm(
                      tester,
                      capture,
                      '${offer.scopeValue}-${width.toInt()}-$locale-${dark ? 'dark' : 'light'}-overview',
                    );
                  }
                  final target = offer.scope == RentalScope.entireProperty
                      ? find.byType(AddPropertyDetailsSection)
                      : find.byKey(
                          ValueKey(
                            '${offer.scope == RentalScope.bed ? offer.bedRef : offer.roomRefs.first}:name',
                          ),
                        );
                  await tester.ensureVisible(target);
                  await tester.pumpAndSettle();
                  expect(tester.takeException(), isNull);
                  await captureAccommodationForm(
                    tester,
                    capture,
                    '${offer.scopeValue}-${width.toInt()}-$locale-${dark ? 'dark' : 'light'}-scale$scale',
                  );
                }
              }
            }
          }
        }
      }
      expect(verified, 288);
    },
  );

  testWidgets(
    'room validation accepts unit details without requiring hidden property totals',
    (tester) async {
      addTearDown(tester.view.reset);
      var proceeded = 0;
      final inventory = rentalInventory(offers: [independentRooms.first])
          .copyWith(
            rooms: [
              rentalRooms.first.copyWith(
                capacity: 0,
                draftDetails: const RentalRoomDraftDetails(area: 'NaN'),
              ),
            ],
          );
      await pump(
        tester,
        _ConditionalBasicsHarness(
          form: rentalForm(
            inventory,
          ).copyWith(bedrooms: '', bathrooms: '', space: ''),
          onNext: () => proceeded++,
        ),
        locale: 'en',
      );
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyNextPhotos));
      await tester.pumpAndSettle();
      expect(proceeded, 0);
      expect(find.text(LocaleKeys.rentalRoomAreaInvalid), findsWidgets);
      expect(find.text(LocaleKeys.rentalRoomCapacityInvalid), findsWidgets);
      final area = find.byKey(const ValueKey('room-a:area'));
      await tester.ensureVisible(area);
      await tester.enterText(area, '18.5');
      await tester.pump();
      final capacity = find.byKey(const ValueKey('room-a:capacity'));
      await tester.ensureVisible(capacity);
      await tester.enterText(capacity, '2');
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyNextPhotos));
      await tester.pumpAndSettle();
      expect(proceeded, 1);
      expect(find.byType(AddPropertyDetailsSection), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    },
  );
  testWidgets(
    'unit media associates an exact bed photo without assigning it to the shared room',
    (tester) async {
      addTearDown(tester.view.reset);
      final form = ValueNotifier(
        rentalForm(rentalInventory()).copyWith(
          photoDrafts: const [
            OwnerPropertyPhotoDraft(draftKey: 'photo-local-a', name: 'Bed A'),
            OwnerPropertyPhotoDraft(
              draftKey: 'photo-local-b',
              name: 'Shared kitchen',
            ),
          ],
        ),
      );
      addTearDown(form.dispose);
      await pump(
        tester,
        ValueListenableBuilder<OwnerAddPropertyFormState>(
          valueListenable: form,
          builder: (_, value, _) => SingleChildScrollView(
            child: RentalAccommodationMediaSection(
              form: value,
              onChanged: (v) => form.value = v,
            ),
          ),
        ),
        locale: 'ar',
        scale: 2,
        width: 320,
        dark: true,
      );
      final check = find.byType(CheckboxListTile).first;
      await tester.ensureVisible(check);
      await tester.tap(check);
      await tester.pumpAndSettle();
      expect(
        form
            .value
            .rentalInventory!
            .rooms
            .first
            .beds
            .first
            .draftDetails
            .photoRefs,
        ['photo-local-a'],
      );
      expect(
        form.value.rentalInventory!.rooms.first.draftDetails.photoRefs,
        isEmpty,
      );
      expect(form.value.rentalInventory!.draftDetails.photoRefs, isEmpty);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'review media names only rooms included in the advertised offers',
    (tester) async {
      addTearDown(tester.view.reset);
      await pump(
        tester,
        RentalMediaReviewSummary(
          form: rentalForm(rentalInventory(offers: [independentRooms.first])),
        ),
      );
      expect(find.textContaining(rentalRooms.first.name), findsOneWidget);
      expect(find.textContaining(rentalRooms[1].name), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'a property with one offer requires choosing and confirming accommodation',
    (tester) async {
      addTearDown(tester.view.reset);
      String? selected;
      RentalSelection? confirmed;
      final choice = ValueNotifier<String?>(null);
      addTearDown(choice.dispose);
      await pump(
        tester,
        SingleChildScrollView(
          child: ValueListenableBuilder<String?>(
            valueListenable: choice,
            builder: (_, id, _) => RentalOfferPicker(
              propertyId: 'property-a',
              inventory: rentalInventory(),
              selectedId: id,
              onSelected: (id) {
                selected = id;
                choice.value = id;
              },
              onConfirmed: (selection) => confirmed = selection,
            ),
          ),
        ),
      );
      expect(find.byType(RentalSelectionPanel), findsNothing);
      await tester.tap(find.byType(ListTile).first);
      expect(selected, 'offer-bed-a1');
      expect(confirmed, isNull);
      await tester.pumpAndSettle();
      final confirmation = find.text(LocaleKeys.rentalConfirmAccommodation);
      await tester.ensureVisible(confirmation);
      await tester.tap(confirmation);
      expect(confirmed?.offerId, 'offer-bed-a1');
      expect(confirmed?.bedId, 'bed-a1');
      expect(confirmed?.scopeValue, 'bed');
    },
  );
  testWidgets(
    'a missing selected offer stays unavailable rather than selecting another',
    (tester) async {
      addTearDown(tester.view.reset);
      String? selected;
      await pump(
        tester,
        SingleChildScrollView(
          child: RentalOfferPicker(
            propertyId: 'property-a',
            inventory: rentalInventory(),
            selectedId: 'removed-offer',
            onSelected: (id) => selected = id,
          ),
        ),
      );
      expect(find.text(LocaleKeys.rentalNotAvailable), findsOneWidget);
      expect(find.byType(RentalSelectionPanel), findsNothing);
      expect(selected, isNull);
    },
  );
  testWidgets(
    'owner inventory changes keep field state and separate independent offers',
    (tester) async {
      addTearDown(tester.view.reset);
      final value = ValueNotifier<RentalInventory>(
        rentalInventory(offers: independentRooms),
      );
      addTearDown(value.dispose);
      await pump(
        tester,
        ValueListenableBuilder<RentalInventory>(
          valueListenable: value,
          builder: (_, inventory, _) => SingleChildScrollView(
            child: RentalInventoryEditor(
              inventory: inventory,
              totalRooms: 3,
              photos: rentalForm(inventory).photoDrafts,
              onChanged: (updated) => value.value = updated,
            ),
          ),
        ),
      );
      final roomName = find.byKey(const ValueKey('room-a:name'));
      await tester.ensureVisible(roomName);
      await tester.enterText(roomName, 'الغرفة الشرقية');
      await tester.pump();
      expect(value.value.rooms.first.name, 'الغرفة الشرقية');
      expect(value.value.offers, hasLength(2));
      expect(value.value.offers.first.roomRefs, ['room-a']);
      expect(value.value.offers.last.terms.price, '2200');
    },
  );
  testWidgets('historical bed summary shows original accommodation and terms', (
    tester,
  ) async {
    addTearDown(tester.view.reset);
    final selection = RentalSelection.fromOffer(
      propertyId: 'property-a',
      inventory: rentalInventory(),
      offer: bedOffer,
    );
    await pump(
      tester,
      SingleChildScrollView(
        child: RentalSelectionPanel(selection: selection, historical: true),
      ),
    );
    expect(find.text(LocaleKeys.rentalHistoricalTerms), findsOneWidget);
    expect(find.textContaining('السرير أ١'), findsWidgets);
    expect(find.textContaining('9000'), findsNothing);
  });
}

class _Translations extends AssetLoader {
  const _Translations(this.values);
  final Map<String, Map<String, dynamic>> values;
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      values[locale.languageCode]!;
}

class _ConditionalBasicsHarness extends StatefulWidget {
  const _ConditionalBasicsHarness({required this.form, this.onNext});
  final OwnerAddPropertyFormState form;
  final VoidCallback? onNext;
  @override
  State<_ConditionalBasicsHarness> createState() =>
      _ConditionalBasicsHarnessState();
}

class _ConditionalBasicsHarnessState extends State<_ConditionalBasicsHarness> {
  late final ValueNotifier<OwnerAddPropertyFormState> _form = ValueNotifier(
    widget.form,
  );
  late final _title = TextEditingController(text: widget.form.title);
  late final _street = TextEditingController(text: widget.form.street);
  late final _bedrooms = TextEditingController(text: widget.form.bedrooms);
  late final _bathrooms = TextEditingController(text: widget.form.bathrooms);
  late final _space = TextEditingController(text: widget.form.space);
  late final _floor = TextEditingController(text: widget.form.floor);
  @override
  void dispose() {
    _form.dispose();
    for (final controller in [
      _title,
      _street,
      _bedrooms,
      _bathrooms,
      _space,
      _floor,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(
    BuildContext context,
  ) => ValueListenableBuilder<OwnerAddPropertyFormState>(
    valueListenable: _form,
    builder: (_, form, _) => AppScaffold(
      title: RentalOfferLabels.formTitle(form.rentalScope, editing: true),
      body: AddPropertyBasicsPage(
        key: ValueKey((form.rentalScope, form.selectedOffer?.reference)),
        form: form,
        onFormChanged: (v) => _form.value = v,
        rentalScopeSelector: RentalScopeSelector(
          inventory: form.rentalInventory,
          selectedScope: form.rentalScope,
          selectedOfferPersisted: form.selectedOffer?.id.isNotEmpty == true,
          onChanged: (inventory) =>
              _form.value = _form.value.copyWith(rentalInventory: inventory),
          onScopeSelected: (scope) => _form.value =
              OwnerAccommodationDraftData.chooseScope(_form.value, scope),
          onLegacy: () =>
              _form.value = _form.value.copyWith(clearRentalInventory: true),
        ),
        titleController: _title,
        streetController: _street,
        bedroomsController: _bedrooms,
        bathroomsController: _bathrooms,
        spaceController: _space,
        floorController: _floor,
        selectedGovernorate: const OwnerPropertyLocationModel.initial()
            .copyWith(id: form.governorateId, name: form.governorate),
        selectedCity: const OwnerPropertyLocationModel.initial().copyWith(
          id: form.districtId,
          name: form.district,
        ),
        locationDropdownGeneration: 0,
        onPropertyTypeSelected: (type) => _form.value = _form.value.copyWith(
          propertyType: type.name,
          propertyTypeValue: type.slug,
        ),
        onTitleChanged: (v) => _form.value = _form.value.copyWith(title: v),
        onGovernorateChanged: (v) {
          if (_form.value.governorateId != v.id ||
              _form.value.governorate != v.name) {
            _form.value = _form.value.copyWith(
              governorateId: v.id,
              governorate: v.name,
            );
          }
        },
        onCityChanged: (v) {
          if (_form.value.districtId != v.id ||
              _form.value.district != v.name) {
            _form.value = _form.value.copyWith(
              districtId: v.id,
              district: v.name,
            );
          }
        },
        onStreetChanged: (v) => _form.value = _form.value.copyWith(street: v),
        onBedroomsChanged: (v) =>
            _form.value = _form.value.copyWith(bedrooms: v),
        onBathroomsChanged: (v) =>
            _form.value = _form.value.copyWith(bathrooms: v),
        onSpaceChanged: (v) => _form.value = _form.value.copyWith(space: v),
        onFloorChanged: (v) => _form.value = _form.value.copyWith(floor: v),
        onLocationSelected: (v) =>
            _form.value = _form.value.copyWith(location: v),
        onNext: widget.onNext ?? () {},
      ),
    ),
  );
}

class _FormRepository implements BaseRepository {
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async => Success(
    BaseModel<T>(
      key: '',
      msg: '',
      data: params.mapper!(
        params.api == ApiConstants.propertyTypes
            ? {
                'count': 1,
                'results': [
                  {'id': 'apartment', 'name': 'Apartment', 'slug': 'apartment'},
                ],
              }
            : {'count': 0, 'results': []},
      ),
    ),
  );
  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

Future<void> captureAccommodationForm(
  WidgetTester tester,
  GlobalKey boundaryKey,
  String name,
) async {
  await tester.runAsync(() async {
    final boundary =
        boundaryKey.currentContext!.findRenderObject()!
            as RenderRepaintBoundary;
    final rendered = await boundary.toImage(pixelRatio: 1);
    final bytes = await rendered.toByteData(format: ui.ImageByteFormat.png);
    final directory = Directory(
      '${Directory.systemTemp.path}/sokoun-accommodation-form-renders',
    )..createSync(recursive: true);
    File(
      '${directory.path}/$name.png',
    ).writeAsBytesSync(bytes!.buffer.asUint8List());
    rendered.dispose();
  });
}
