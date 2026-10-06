import 'dart:async';
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
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:google_maps_flutter_platform_interface/google_maps_flutter_platform_interface.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_location.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/property_location_data.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/property_location_cubit.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/property_location_picker_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_map_section.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'helpers/home_page_test_dependencies.dart';

const _point = PropertyLocation(latitude: 30.0444, longitude: 31.2357);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _LocationSource source;
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold']) {
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
    GoogleMapsFlutterPlatform.instance = _MapSurface();
  });
  setUp(() async {
    GoogleMapsFlutterPlatform.instance = _MapSurface();
    await injector.reset();
    registerHomePageTestDependencies();
    source = _LocationSource();
    injector.registerSingleton<PropertyLocationDataSource>(source);
  });
  tearDown(() => injector.reset());

  test(
    'coordinates are valid independently of geocoding and zero is allowed',
    () {
      expect(const PropertyLocation(latitude: 0, longitude: 0).isValid, isTrue);
      expect(
        const PropertyLocation(latitude: 91, longitude: 0).isValid,
        isFalse,
      );
      expect(PropertyLocation.fromJson({}).isValid, isFalse);
      expect(PropertyLocation.fromJson(_point.toJson()), _point);
    },
  );

  test(
    'editing restores coordinates rather than inferring a pin from text',
    () {
      final property = const PropertyDetailsModel.initial().copyWith(
        latitude: '30.0444',
        longitude: '31.2357',
        district: 'Maadi',
      );
      final seed = OwnerAddPropertyMapper.fromProperty(property);
      expect(seed.form.location, _point);
      expect(seed.form.street, 'Maadi');
      expect(
        OwnerAddPropertyMapper.fromProperty(
          property.copyWith(latitude: ''),
        ).form.isLocationSelected,
        isFalse,
      );
      expect(
        seed.form.copyWith(clearLocation: true).isLocationSelected,
        isFalse,
      );
      expect(
        OwnerAddPropertyFormState.initial()
            .copyWith(street: 'Cairo')
            .isLocationSelected,
        isFalse,
      );
    },
  );

  test('a late search cannot replace a manually selected pin', () async {
    final cubit = PropertyLocationCubit(source: source);
    addTearDown(cubit.close);
    source.searchGate = Completer<List<PropertyLocation>>();
    final pending = cubit.search('Cairo');
    cubit.select(_point);
    source.searchGate!.complete([
      const PropertyLocation(latitude: 31, longitude: 32),
    ]);
    await pending;
    expect(cubit.data.selected?.latitude, _point.latitude);
    expect(cubit.data.results, isEmpty);
    expect(cubit.isLoading, isFalse);
  });

  test(
    'failed reverse geocoding and denied permissions preserve the pin',
    () async {
      source.failAddress = true;
      source.failure = PropertyLocationFailure.permissionDeniedForever;
      final cubit = PropertyLocationCubit(source: source);
      addTearDown(cubit.close);
      cubit.select(_point);
      await cubit.locate();
      expect(cubit.data.selected, _point);
      expect(
        cubit.data.failure,
        PropertyLocationFailure.permissionDeniedForever,
      );
      await cubit.openSettings();
      expect(source.appSettings, isTrue);
    },
  );

  test('closing while locating ignores completion', () async {
    source.locationGate = Completer<PropertyLocation>();
    final cubit = PropertyLocationCubit(source: source);
    final pending = cubit.locate();
    await cubit.close();
    source.locationGate!.complete(_point);
    await pending;
    expect(cubit.data.selected, isNull);
  });

  test('unavailable settings preserves the selected location', () async {
    source.failSettings = true;
    final cubit = PropertyLocationCubit(source: source);
    addTearDown(cubit.close);
    cubit.select(_point);
    await cubit.openSettings();
    expect(cubit.data.selected?.latitude, _point.latitude);
    expect(cubit.data.failure, PropertyLocationFailure.unavailable);
  });

  testWidgets('keyboard and rotation preserve the selected pin', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      _app(
        const PropertyLocationPickerScreen(initialLocation: _point),
        'ar',
        1.3,
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byType(TextField));
    tester.view.viewInsets = const FakeViewPadding(bottom: 320);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    tester.view.viewInsets = FakeViewPadding.zero;
    tester.view.physicalSize = const Size(844, 390);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(
      tester.widget<GoogleMap>(find.byType(GoogleMap)).markers.single.position,
      const LatLng(30.0444, 31.2357),
    );
  });

  testWidgets(
    'cancel preserves the form and confirmation returns the chosen point',
    (tester) async {
      PropertyLocation? result;
      await tester.pumpWidget(
        _app(
          Scaffold(
            body: AddPropertyMapSection(
              location: null,
              query: '',
              onLocationSelected: (location) => result = location,
            ),
          ),
          'en',
          1,
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.ownerAddPropertySelectLocation));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<DefaultButton>(
              find.widgetWithText(DefaultButton, LocaleKeys.propertyMapConfirm),
            )
            .disabled,
        isTrue,
      );
      tester.widget<GoogleMap>(find.byType(GoogleMap)).onTap!(
        const LatLng(30, 31),
      );
      await tester.pumpAndSettle();
      Go.back();
      await tester.pumpAndSettle();
      expect(result, isNull);
      await tester.tap(find.text(LocaleKeys.ownerAddPropertySelectLocation));
      await tester.pumpAndSettle();
      tester.widget<GoogleMap>(find.byType(GoogleMap)).onTap!(
        const LatLng(30, 31),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.propertyMapConfirm));
      await tester.pumpAndSettle();
      expect(result?.latitude, 30);
      expect(result?.longitude, 31);
    },
  );

  testWidgets(
    'search moves the SDK camera to the first result and allows another result',
    (tester) async {
      final map = _CameraMapSurface();
      GoogleMapsFlutterPlatform.instance = map;
      const otherPoint = PropertyLocation(latitude: 31.2, longitude: 29.9);
      source.results = [_point, otherPoint];
      await tester.pumpWidget(
        _app(const PropertyLocationPickerScreen(), 'en', 1),
      );
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), 'Cairo');
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();
      expect(find.byType(ListTile), findsNWidgets(2));
      expect(
        map.cameraCalls.last.arguments['cameraUpdate'],
        CameraUpdate.newLatLngZoom(const LatLng(30.0444, 31.2357), 17).toJson(),
      );
      expect(
        tester
            .widget<GoogleMap>(find.byType(GoogleMap))
            .markers
            .single
            .position,
        const LatLng(30.0444, 31.2357),
      );
      expect(find.byType(PropertyLocationPickerScreen), findsOneWidget);
      await tester.tap(find.byType(ListTile).last);
      await tester.pumpAndSettle();
      expect(
        map.cameraCalls.last.arguments['cameraUpdate'],
        CameraUpdate.newLatLngZoom(const LatLng(31.2, 29.9), 17).toJson(),
      );
      await tester.enterText(find.byType(TextField), 'Alexandria');
      expect(find.byType(ListTile), findsNothing);
      final context = tester.element(find.byType(GoogleMap));
      expect(
        context.read<PropertyLocationCubit>().data.selected?.latitude,
        31.2,
      );
    },
  );

  test('empty search keeps the existing pin and reports no results', () async {
    final cubit = PropertyLocationCubit(source: source);
    addTearDown(cubit.close);
    cubit.select(_point);
    await cubit.search('Unknown address');
    expect(cubit.data.selected?.latitude, _point.latitude);
    expect(cubit.data.results, isEmpty);
    expect(cubit.data.failure, PropertyLocationFailure.noResults);
  });

  for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      for (final locale in ['ar', 'en']) {
        testWidgets('picker fits $locale $width at $scale', (tester) async {
          tester.view.physicalSize = Size(width, 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          await tester.pumpWidget(
            _app(
              const PropertyLocationPickerScreen(initialLocation: _point),
              locale,
              scale,
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          expect(find.text(_point.coordinates), findsOneWidget);
          await tester.tap(find.text(LocaleKeys.propertyMapSatellite));
          await tester.pumpAndSettle();
          expect(
            tester.widget<GoogleMap>(find.byType(GoogleMap)).mapType,
            MapType.hybrid,
          );
          if (width == 390 &&
              scale == 1 &&
              Platform.environment['CAPTURE_MAP'] == '1') {
            final boundary = tester.renderObject<RenderRepaintBoundary>(
              find.byType(RepaintBoundary).first,
            );
            await tester.runAsync(() async {
              final image = await boundary.toImage(pixelRatio: 1);
              final bytes = await image.toByteData(
                format: ui.ImageByteFormat.png,
              );
              await File(
                '/tmp/sokoun-map-controls-$locale.png',
              ).writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
}

Widget _app(Widget child, String locale, double scale) => EasyLocalization(
  supportedLocales: const [Locale('ar'), Locale('en')],
  path: 'unused',
  startLocale: Locale(locale),
  saveLocale: false,
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    enableScaleWH: () => false,
    enableScaleText: () => false,
    designSize: const Size(360, 690),
    builder: (context, _) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      theme: SokounTheme.light,
      locale: context.locale,
      supportedLocales: context.supportedLocales,
      localizationsDelegates: context.localizationDelegates,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(
          context,
        ).copyWith(textScaler: TextScaler.linear(scale)),
        child: child!,
      ),
      home: child,
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

class _LocationSource implements PropertyLocationDataSource {
  Completer<List<PropertyLocation>>? searchGate;
  Completer<PropertyLocation>? locationGate;
  List<PropertyLocation> results = [];
  bool failAddress = false;
  bool failSettings = false;
  bool? appSettings;
  PropertyLocationFailure? failure;
  @override
  Future<String> addressFor(PropertyLocation location) async {
    if (failAddress) throw StateError('Offline');
    return 'Maadi Cairo';
  }

  @override
  Future<PropertyLocation> currentLocation() async {
    if (failure != null) throw failure!;
    return locationGate?.future ?? Future.value(_point);
  }

  @override
  Future<bool> openSettings({required bool appSettings}) async {
    if (failSettings) throw StateError('Settings unavailable');
    this.appSettings = appSettings;
    return true;
  }

  @override
  Future<List<PropertyLocation>> search(String query) async =>
      searchGate?.future ?? Future.value(results);
}

/// Native tiles require a device. Keep this surface explicit in visual captures.
class _MapSurface extends GoogleMapsFlutterPlatform {
  @override
  Widget buildViewWithConfiguration(
    int creationId,
    PlatformViewCreatedCallback onPlatformViewCreated, {
    required MapWidgetConfiguration widgetConfiguration,
    MapConfiguration mapConfiguration = const MapConfiguration(),
    MapObjects mapObjects = const MapObjects(),
  }) => const ColoredBox(
    color: AppColors.grayBackground,
    child: Center(child: Text('Native map surface')),
  );
}

/// Exercises the actual SDK controller while replacing only the native surface.
class _CameraMapSurface extends MethodChannelGoogleMapsFlutter {
  final _createdMaps = <int>{};
  final cameraCalls = <MethodCall>[];

  @override
  Future<void> updateGroundOverlays(
    GroundOverlayUpdates groundOverlayUpdates, {
    required int mapId,
  }) async {}

  @override
  Widget buildViewWithConfiguration(
    int creationId,
    PlatformViewCreatedCallback onPlatformViewCreated, {
    required MapWidgetConfiguration widgetConfiguration,
    MapConfiguration mapConfiguration = const MapConfiguration(),
    MapObjects mapObjects = const MapObjects(),
  }) {
    if (_createdMaps.add(creationId)) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(
            MethodChannel('plugins.flutter.io/google_maps_$creationId'),
            (call) async {
              if (call.method == 'camera#animate') cameraCalls.add(call);
              return null;
            },
          );
      WidgetsBinding.instance.addPostFrameCallback(
        (_) => onPlatformViewCreated(creationId),
      );
    }
    return const ColoredBox(color: AppColors.grayBackground);
  }
}
