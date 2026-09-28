import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/data/property_photo_gallery_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_photo_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_photos/photo_save_button.dart';
import 'package:toastification/toastification.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const galleryChannel = MethodChannel('gal');
  const preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const imageUrl = 'https://example.com/property-photo.png';
  final imageBytes = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
  );
  late Directory temporaryDirectory;
  late File image;
  late List<MethodCall> galleryCalls;
  late bool accessGranted;
  late int downloads;
  PlatformException? saveError;
  late PropertyPhotoGalleryData galleryData;

  setUpAll(() async {
    temporaryDirectory = await Directory.systemTemp.createTemp('sokoun-photo-');
    image = await File(
      '${temporaryDirectory.path}/photo.png',
    ).writeAsBytes(imageBytes);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
  });

  setUp(() {
    galleryCalls = [];
    accessGranted = true;
    downloads = 0;
    saveError = null;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(galleryChannel, (call) async {
          galleryCalls.add(call);
          if (call.method == 'requestAccess') return accessGranted;
          if (call.method == 'putImageBytes' && saveError != null) {
            throw saveError!;
          }
          return null;
        });
    galleryData = PropertyPhotoGalleryData(
      loadImage: (url) async {
        expect(url, imageUrl);
        downloads++;
        return image;
      },
    );
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(galleryChannel, null);
  });

  tearDownAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
    await temporaryDirectory.delete(recursive: true);
  });

  test('saves the requested image bytes into the named Sokoun album', () async {
    expect(await galleryData.saveImage(imageUrl), isTrue);

    final MethodCall save = galleryCalls.singleWhere(
      (call) => call.method == 'putImageBytes',
    );
    expect(save.arguments['album'], 'سكون');
    expect(save.arguments['bytes'], imageBytes);
    expect(save.arguments['name'], startsWith('sokoun_'));
    expect(downloads, 1);
    expect(
      galleryCalls
          .where((call) => call.method == 'requestAccess')
          .every((call) => call.arguments['toAlbum'] == true),
      isTrue,
    );
  });

  test('permission denial does not download or write the photo', () async {
    accessGranted = false;

    expect(await galleryData.saveImage(imageUrl), isFalse);
    expect(downloads, 0);
    expect(galleryCalls.map((call) => call.method), ['requestAccess']);
  });

  test('storage failure does not emit success', () async {
    saveError = PlatformException(code: 'NOT_ENOUGH_SPACE');
    final cubit = PropertyPhotoSaveCubit(galleryData: galleryData);
    addTearDown(cubit.close);

    await cubit.saveImage(imageUrl);

    expect(cubit.state.status.isError, isTrue);
    expect(cubit.state.errorMessage, LocaleKeys.tenantPropertyPhotoStorageFull);
  });

  test('failed image download does not write to the gallery', () async {
    final cubit = PropertyPhotoSaveCubit(
      galleryData: PropertyPhotoGalleryData(
        loadImage: (_) => Future.error(const SocketException('offline')),
      ),
    );
    addTearDown(cubit.close);

    await cubit.saveImage(imageUrl);

    expect(cubit.state.status.isError, isTrue);
    expect(
      galleryCalls.where((call) => call.method == 'putImageBytes'),
      isEmpty,
    );
  });

  test('ignores duplicate saves and completion after disposal', () async {
    final result = Completer<bool>();
    final data = _PendingGalleryData(result.future);
    final cubit = PropertyPhotoSaveCubit(galleryData: data);

    final Future<void> firstSave = cubit.saveImage(imageUrl);
    await cubit.saveImage(imageUrl);
    expect(data.savedUrls, [imageUrl]);
    expect(cubit.state.status.isLoading, isTrue);

    await cubit.close();
    result.complete(true);
    await firstSave;
    expect(cubit.isClosed, isTrue);
  });

  testWidgets('viewer download follows arrows and thumbnail selection', (
    tester,
  ) async {
    final property = TenantPropertyDetailsContent.fromModel(
      PropertyDetailsModel.fromJson({
        'main_image': imageUrl,
        'images': [
          {'image': 'https://example.com/second.png', 'name': 'Second photo'},
          {'image': 'https://example.com/third.png', 'name': 'Third photo'},
        ],
      }),
    );
    await tester.pumpWidget(
      _localizedScreen(
        TenantPropertyPhotosScreen(property: property, initialIndex: 1),
      ),
    );
    await tester.pump();
    await tester.pump();

    void expectDownloadFor(String url) {
      expect(find.byIcon(Icons.download_rounded), findsOneWidget);
      expect(tester.widget<CachedImage>(find.byType(CachedImage)).url, url);
      expect(
        tester
            .widget<TenantPropertyPhotoSaveButton>(
              find.byType(TenantPropertyPhotoSaveButton),
            )
            .imageUrl,
        url,
      );
    }

    expectDownloadFor(property.imageUrls[1]);
    await tester.tap(find.byIcon(Icons.chevron_right_rounded));
    await tester.pump();
    expectDownloadFor(property.imageUrls[2]);

    await tester.tap(find.byIcon(Icons.chevron_left_rounded));
    await tester.pump();
    expectDownloadFor(property.imageUrls[1]);

    await tester.tap(find.byIcon(Icons.image_outlined).first);
    await tester.pump();
    expectDownloadFor(property.imageUrls.first);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('viewer hides download when there is no image', (tester) async {
    await tester.pumpWidget(
      _localizedScreen(
        TenantPropertyPhotosScreen(
          property: TenantPropertyDetailsContent.fromModel(
            const PropertyDetailsModel.initial(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.download_rounded), findsNothing);
    expect(find.byIcon(Icons.apartment_outlined), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final bool saved in [true, false]) {
    testWidgets('save button shows the actual result: $saved', (tester) async {
      final result = Completer<bool>();
      final data = _PendingGalleryData(result.future);
      final cubit = PropertyPhotoSaveCubit(galleryData: data);
      addTearDown(cubit.close);
      await tester.pumpWidget(_screen(cubit: cubit, imageUrl: imageUrl));
      await tester.pumpAndSettle();

      await tester.tap(find.byTooltip('حفظ الصورة'));
      await tester.pump();
      await tester.pump();

      expect(data.savedUrls, [imageUrl]);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(
        tester.widget<IconButton>(find.byType(IconButton)).onPressed,
        isNull,
      );
      expect(find.text('تم حفظ الصورة في مجلد سكون'), findsNothing);

      result.complete(saved);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(
        find.text('تم حفظ الصورة في مجلد سكون'),
        saved ? findsOneWidget : findsNothing,
      );
      if (!saved) {
        expect(
          find.text('اسمح بالوصول إلى الصور لحفظها في سكون'),
          findsOneWidget,
        );
      }
      expect(tester.takeException(), isNull);
      toastification.dismissAll(delayForAnimation: false);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(seconds: 5));
    });
  }
}

Widget _screen({
  required PropertyPhotoSaveCubit cubit,
  required String imageUrl,
}) {
  return _localizedScreen(
    Scaffold(
      body: BlocProvider.value(
        value: cubit,
        child: Center(child: TenantPropertyPhotoSaveButton(imageUrl: imageUrl)),
      ),
    ),
  );
}

Widget _localizedScreen(Widget screen) {
  return EasyLocalization(
    supportedLocales: const [Locale('ar')],
    startLocale: const Locale('ar'),
    path: 'unused',
    assetLoader: const _Translations(),
    child: ScreenUtilInit(
      designSize: const Size(390, 844),
      builder: (context, _) => MaterialApp(
        navigatorKey: Go.navigatorKey,
        localizationsDelegates: context.localizationDelegates,
        supportedLocales: context.supportedLocales,
        locale: context.locale,
        home: screen,
      ),
    ),
  );
}

class _PendingGalleryData extends PropertyPhotoGalleryData {
  _PendingGalleryData(this.result)
    : super(loadImage: (_) => throw UnimplementedError());

  final Future<bool> result;
  final List<String> savedUrls = [];

  @override
  Future<bool> saveImage(String imageUrl) {
    savedUrls.add(imageUrl);
    return result;
  }
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'tenant_property_photo_save': 'حفظ الصورة',
    'tenant_property_photo_saving': 'جارٍ حفظ الصورة',
    'tenant_property_photo_saved': 'تم حفظ الصورة في مجلد @album',
    'tenant_property_photo_permission_denied':
        'اسمح بالوصول إلى الصور لحفظها في @album',
    'success_done': 'تم بنجاح',
    'operation_faild': 'حدث خطأ',
  };
}
