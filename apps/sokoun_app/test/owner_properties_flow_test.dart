import 'package:toastification/toastification.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_location.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_review_sheet.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_edit_review_sheet.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_property_flow_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/imports.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_video_picker.dart';
import 'package:video_player_platform_interface/video_player_platform_interface.dart';

import 'helpers/fake_property_video_platform.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _OwnerPropertiesRepository repository;

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );
  const MethodChannel connectivityStatusChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity_status',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, (call) async {
          return call.method == 'check' ? <String>['wifi'] : null;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityStatusChannel, (call) async {
          return null;
        });
    await EasyLocalization.ensureInitialized();
  });

  setUp(() async {
    toastification.managers.clear();
    await injector.reset();
    repository = _OwnerPropertiesRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });

  tearDown(() => injector.reset());

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityStatusChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _OwnerPropertiesAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: screen,
          );
        },
      ),
    );
  }

  void configurePhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  Future<void> selectPropertyTab(
    WidgetTester tester,
    OwnerPropertyFilter filter,
  ) async {
    final Finder tab = find.descendant(
      of: find.byType(TabBar),
      matching: find.text(filter.label),
    );
    await tester.ensureVisible(tab);
    await tester.pump();
    await tester.tap(tab);
    await tester.pump();
    // A refreshed card may load a remote thumbnail; check the tab transition
    // without waiting for that unrelated image placeholder to stop animating.
    await tester.pump(const Duration(milliseconds: 400));
  }

  List<OwnerPropertyContent> ownerPropertiesFixture() {
    return const [
      OwnerPropertyContent(
        id: 'nasr-city-furnished',
        title: 'شقة مفروشة — مدينة نصر',
        mainImage: '',
        location: 'مدينة نصر، القاهرة',
        monthlyPrice: 6500,
        views: 142,
        visitRequests: 3,
        bedrooms: 2,
        area: 120,
        description: 'شقة مفروشة بإضاءة طبيعية ومرافق متكاملة',
        photoCount: 12,
        status: OwnerPropertyStatus.verified,
      ),
      OwnerPropertyContent(
        id: 'fifth-settlement-studio',
        title: 'ستوديو — التجمع الخامس',
        mainImage: '',
        location: 'التجمع الخامس، القاهرة',
        monthlyPrice: 4200,
        views: 67,
        visitRequests: 0,
        bedrooms: 1,
        area: 65,
        description: 'ستوديو حديث قريب من الخدمات والمواصلات',
        photoCount: 8,
        status: OwnerPropertyStatus.pending,
      ),
      OwnerPropertyContent(
        id: 'mohandessin-three-bed',
        title: 'شقة 3 غرف — المهندسين',
        mainImage: '',
        location: 'المهندسين، الجيزة',
        monthlyPrice: 8800,
        views: 0,
        visitRequests: 0,
        bedrooms: 3,
        area: 165,
        description: 'شقة واسعة من ثلاث غرف بإطلالة هادئة',
        photoCount: 10,
        status: OwnerPropertyStatus.hidden,
      ),
    ];
  }

  Future<void> openEditReview(WidgetTester tester) async {
    await tester.tap(find.text('التالي — الصور'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
    await tester.pumpAndSettle();
    final requestsBeforeReview = repository.updateRequestCount;
    await tester.tap(find.text(LocaleKeys.ownerPropertyReviewAction));
    await tester.pumpAndSettle();
    expect(find.byType(PropertyReviewSheet), findsOneWidget);
    expect(repository.updateRequestCount, requestsBeforeReview);
  }

  Future<void> submitEditFlow(WidgetTester tester) async {
    await openEditReview(tester);
    await tester.tap(find.text('حفظ التعديلات'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(find.byType(PropertyEditReviewSheet), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(PropertyEditReviewSheet),
        matching: find.text('Server saved the property changes'),
      ),
      findsOneWidget,
    );
    toastification.dismissAll(delayForAnimation: false);
    await tester.pump(const Duration(seconds: 1));
    await tester.tap(find.text(LocaleKeys.ownerPropertyEditReviewDone));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
  }

  Future<void> prepareCreateFlow(
    WidgetTester tester, {
    bool addCaptions = true,
    bool addVideo = true,
    bool recordVideo = false,
  }) async {
    configurePhoneViewport(tester);
    final Directory images = Directory.systemTemp.createTempSync(
      'owner-photos-',
    );
    final List<int> bytes = base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
    );
    final List<String> paths = List.generate(10, (index) {
      final File file = File('${images.path}/photo-$index.png');
      file.writeAsBytesSync(bytes);
      return file.path;
    });
    final video = File('${images.path}/tour.mp4')
      ..writeAsBytesSync(utf8.encode('video upload bytes'));
    final videoPlatform = FakePropertyVideoPlatform();
    final originalVideoPlatform = VideoPlayerPlatform.instance;
    if (addVideo) VideoPlayerPlatform.instance = videoPlatform;
    final pickedVideos = <MethodCall>[];
    const MethodChannel picker = MethodChannel(
      'plugins.flutter.io/image_picker',
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(picker, (call) async {
          if (call.method == 'pickVideo') {
            pickedVideos.add(call);
            return video.path;
          }
          return call.method == 'pickMultiImage' ? paths : paths.first;
        });
    addTearDown(() {
      if (addVideo) VideoPlayerPlatform.instance = originalVideoPlatform;
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(picker, null);
      images.deleteSync(recursive: true);
    });

    await tester.pumpWidget(buildScreen(const OwnerPropertyFlowScreen()));
    await tester.pumpAndSettle();
    final AddPropertyBasicsPage basics = tester.widget(
      find.byType(AddPropertyBasicsPage),
    );
    basics.onPropertyTypeSelected(
      const PropertyTypeModel(
        id: 'apartment-type',
        name: 'شقة',
        slug: 'apartment',
        description: '',
      ),
    );
    basics.titleController.text = 'A new apartment';
    basics.onTitleChanged('A new apartment');
    basics.onGovernorateChanged(
      const OwnerPropertyLocationModel.initial().copyWith(
        id: 'cairo',
        name: 'Cairo',
      ),
    );
    basics.onCityChanged(
      const OwnerPropertyLocationModel.initial().copyWith(
        id: 'nasr-city',
        name: 'Nasr City',
      ),
    );
    basics.streetController.text = 'Main street';
    basics.onStreetChanged('Main street');
    basics.bedroomsController.text = '2';
    basics.onBedroomsChanged('2');
    basics.bathroomsController.text = '1';
    basics.onBathroomsChanged('1');
    basics.spaceController.text = '120';
    basics.onSpaceChanged('120');
    basics.floorController.text = '3';
    basics.onFloorChanged('3');
    basics.onLocationSelected(
      const PropertyLocation(latitude: 30.0444, longitude: 31.2357),
    );
    await tester.pump();
    await tester.tap(find.text(LocaleKeys.ownerAddPropertyNextPhotos));
    await tester.pumpAndSettle();
    tester
        .widget<AddPropertyPhotosPage>(find.byType(AddPropertyPhotosPage))
        .onAddPhotos();
    await tester.pumpAndSettle();
    final AddPropertyPhotosPage photos = tester.widget(
      find.byType(AddPropertyPhotosPage),
    );
    expect(photos.photos, hasLength(10));
    if (addVideo) {
      final picker = find.byType(PropertyVideoPicker);
      final upload = find.descendant(
        of: picker,
        matching: find.ancestor(
          of: find.byIcon(Icons.video_library_outlined),
          matching: find.byWidgetPredicate(
            (widget) => widget is OutlinedButton,
          ),
        ),
      );
      final record = find.descendant(
        of: picker,
        matching: find.ancestor(
          of: find.byIcon(Icons.videocam_outlined),
          matching: find.byWidgetPredicate(
            (widget) => widget is OutlinedButton,
          ),
        ),
      );
      expect(upload.hitTestable(), findsOneWidget);
      expect(record.hitTestable(), findsOneWidget);
      await tester.runAsync(() async {
        await tester.tap(recordVideo ? record : upload);
        await Future<void>.delayed(Duration.zero);
      });
      await tester.pumpAndSettle();
      expect(pickedVideos, hasLength(1));
      expect(pickedVideos.single.arguments['source'], recordVideo ? 0 : 1);
      if (recordVideo) {
        expect(pickedVideos.single.arguments['maxDuration'], 60);
      }
      expect(videoPlatform.sources.single.uri, Uri.file(video.path).toString());
      expect(videoPlatform.disposed, 1);
      final selectedForm = tester
          .widget<AddPropertyPhotosPage>(find.byType(AddPropertyPhotosPage))
          .form;
      expect(selectedForm.videoFile?.path, video.path);
      expect(selectedForm.videoDuration, 45);
      expect(selectedForm.isVideoPreparing, isFalse);
      expect(selectedForm.isPhotosReady, isTrue);
    }
    for (int index = 0; addCaptions && index < 10; index++) {
      await tester.enterText(
        find.byType(TextField).at(index * 2),
        'Photo $index',
      );
      await tester.enterText(
        find.byType(TextField).at(index * 2 + 1),
        'Description $index',
      );
    }
    if (!addVideo) return;
    await tester.pump();
    await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
    await tester.pumpAndSettle();
    final AddPropertyPricingPage pricing = tester.widget(
      find.byType(AddPropertyPricingPage),
    );
    pricing.monthlyPriceController.text = '6500';
    pricing.onMonthlyPriceChanged('6500');
    pricing.onSuitableForSelected('singles');
    pricing.rentalDurationController.text = '6';
    pricing.onRentalDurationChanged('6');
    pricing.onRentalUnitChanged('monthly');
    pricing.onAmenityToggled('wifi');
    pricing.descriptionController.text =
        'A comfortable apartment near the metro.';
    pricing.onDescriptionChanged('A comfortable apartment near the metro.');
    await tester.pump();
  }

  Future<void> submitCreateFlow(WidgetTester tester) async {
    await tester.tap(find.text(LocaleKeys.ownerPropertyReviewAction));
    await tester.pumpAndSettle();
    expect(find.byType(PropertyReviewSheet), findsOneWidget);
    await tester.tap(find.text(LocaleKeys.ownerAddPropertySubmitReview));
    await tester.pumpAndSettle();
  }

  testWidgets('Next shows required field errors and keeps the property draft', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(buildScreen(const OwnerPropertyFlowScreen()));
    await tester.pumpAndSettle();
    expect(find.text(LocaleKeys.fillField), findsNothing);
    await tester.tap(find.text(LocaleKeys.ownerAddPropertyNextPhotos));
    await tester.pumpAndSettle();
    expect(find.byType(AddPropertyBasicsPage), findsOneWidget);
    expect(find.byType(AddPropertyPhotosPage), findsNothing);
    expect(find.text(LocaleKeys.fillField), findsWidgets);
    final invalidFields = tester
        .state<FormState>(find.byType(Form))
        .validateGranularly();
    expect(invalidFields, isNotEmpty);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'uploads the cover once, uploads remaining photos concurrently, and retries only failures',
    (tester) async {
      repository.createResponse = Completer<bool>();
      await prepareCreateFlow(tester);
      expect(repository.createRequests, isEmpty);
      expect(repository.imageRequests, isEmpty);
      await submitCreateFlow(tester);
      expect(repository.createRequests, hasLength(1));
      expect(repository.createRequests.single.body!['main_image'], isA<File>());
      expect(
        repository.createRequests.single.body!['main_image_name'],
        'Photo 0',
      );
      expect(
        repository.createRequests.single.body!['main_image_description'],
        'Description 0',
      );
      expect(repository.createRequests.single.body, isNot(contains('images')));
      expect(repository.imageRequests, isEmpty);
      expect(
        tester
            .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
            .isSubmitting,
        isTrue,
      );

      repository.createResponse!.complete(true);
      await tester.pumpAndSettle();
      expect(repository.imageRequests, hasLength(9));
      for (int index = 0; index < 9; index++) {
        final request = repository.imageRequests[index];
        expect(request.api, 'properties/created-property/images/');
        expect(request.httpRequestType, HttpRequestType.post);
        expect(request.isFromData, isTrue);
        expect(request.sendTimeout, ConstantManager.uploadSendTimeout);
        expect(
          request.body!.keys,
          unorderedEquals(['image', 'name', 'description']),
        );
        expect(request.body!['image'], isA<File>());
        expect(request.body!['name'], 'Photo ${index + 1}');
        expect(request.body!['description'], 'Description ${index + 1}');
      }
      // One failure must not finish the batch while other uploads are pending.
      repository.imageResponses.first.complete(false);
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
            .isSubmitting,
        isTrue,
      );
      for (final response in repository.imageResponses.skip(1)) {
        response.complete(true);
      }
      await tester.pumpAndSettle();
      expect(find.byType(AddPropertySubmittedPage), findsNothing);
      final AddPropertyPricingPage details = tester.widget(
        find.byType(AddPropertyPricingPage),
      );
      expect(details.isSubmitting, isFalse);
      expect(
        details.form.photoDrafts.where((photo) => photo.isExisting),
        hasLength(9),
      );

      await submitCreateFlow(tester);
      expect(repository.createRequests, hasLength(1));
      expect(repository.updateRequestCount, 0);
      expect(repository.imageRequests, hasLength(10));
      expect(repository.imageRequests.last.body!['name'], 'Photo 1');
      expect(
        repository.imageRequests.last.api,
        'properties/created-property/images/',
      );
      repository.imageResponses.last.complete(true);
      await tester.pumpAndSettle();
      expect(find.byType(AddPropertySubmittedPage), findsOneWidget);
      expect(tester.takeException(), isNull);

      // Starting another listing must clear the saved property and upload state.
      tester
          .widget<AddPropertySubmittedPage>(
            find.byType(AddPropertySubmittedPage),
          )
          .onAddAnother();
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<AddPropertyBasicsPage>(find.byType(AddPropertyBasicsPage))
            .form
            .photoDrafts,
        isEmpty,
      );
    },
  );

  testWidgets('failed property creation does not start image uploads', (
    tester,
  ) async {
    repository.createResponse = Completer<bool>();
    await prepareCreateFlow(tester);
    await submitCreateFlow(tester);
    repository.createResponse!.complete(false);
    await tester.pumpAndSettle();
    expect(repository.imageRequests, isEmpty);
    expect(find.byType(AddPropertySubmittedPage), findsNothing);
    expect(
      tester
          .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
          .isSubmitting,
      isFalse,
    );
    expect(tester.takeException(), isNull);
  });

  for (final recordVideo in [false, true]) {
    testWidgets(
      'visible ${recordVideo ? 'record' : 'upload'} button creates a listing with video in the same request',
      (tester) async {
        repository.createResponse = Completer<bool>();
        await prepareCreateFlow(
          tester,
          addCaptions: false,
          addVideo: true,
          recordVideo: recordVideo,
        );
        await submitCreateFlow(tester);
        final request = repository.createRequests.single;
        expect(request.api, ApiConstants.createProperty);
        expect(request.body!['main_image_name'], '');
        expect(request.body!['main_image_description'], '');
        expect(request.body!['video'], isA<File>());
        expect(request.body!['video_duration'], 45);
        repository.createResponse!.complete(true);
        await tester.pumpAndSettle();
        expect(repository.imageRequests, hasLength(9));
        final savedForm = tester
            .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
            .form;
        expect(savedForm.videoUrl, 'https://example.com/tour.mp4');
        expect(savedForm.videoFile, isNull);
        for (final request in repository.imageRequests) {
          expect(request.body!['name'], '');
          expect(request.body!['description'], '');
        }
        for (final response in repository.imageResponses) {
          response.complete(true);
        }
        await tester.pumpAndSettle();
        expect(find.byType(AddPropertySubmittedPage), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets(
    'photos and a video are both required before continuing to pricing',
    (tester) async {
      await prepareCreateFlow(tester, addCaptions: false, addVideo: false);
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
      await tester.pumpAndSettle();
      expect(
        tester.widget<AppScaffold>(find.byType(AppScaffold)).title,
        LocaleKeys.ownerPropertiesPhotos,
      );
      final photos = tester.widget<AddPropertyPhotosPage>(
        find.byType(AddPropertyPhotosPage),
      );
      expect(photos.form.isPhotosReady, isFalse);
      expect(repository.createRequests, isEmpty);
      photos.onVideoSelected(
        File('${photos.photos.first.file!.parent.path}/tour.mp4'),
        45,
      );
      photos.onRemovePhoto(0);
      await tester.pumpAndSettle();
      final form = tester
          .widget<AddPropertyPhotosPage>(find.byType(AddPropertyPhotosPage))
          .form;
      expect(form.isVideoReady, isTrue);
      expect(form.photoCount, 9);
      expect(form.isPhotosReady, isFalse);
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
      await tester.pumpAndSettle();
      expect(
        tester.widget<AppScaffold>(find.byType(AppScaffold)).title,
        LocaleKeys.ownerPropertiesPhotos,
      );
      expect(repository.createRequests, isEmpty);
      expect(tester.takeException(), isNull);
    },
  );

  test('maps the owned-properties response', () {
    final OwnerPropertiesResponse response = OwnerPropertiesResponse.fromJson({
      'count': 1,
      'next': null,
      'previous': null,
      'results': [
        {
          'id': 'ade32b4e-8ab3-43b6-927e-65918f628e22',
          'title': 'Cozy Studio Near Metro Station 1',
          'main_image': 'https://example.com/property.jpg',
          'price': '7000.00',
          'status': 'under_review',
          'views_count': 0,
          'visits_count': 1,
        },
      ],
    });

    expect(response.count, 1);
    expect(response.results, hasLength(1));
    expect(response.results.single.monthlyPrice, 7000);
    expect(response.results.single.status, OwnerPropertyStatus.pending);
    expect(response.results.single.views, 0);
    expect(response.results.single.visitRequests, 1);
  });

  test('maps governorate and city lookup responses', () {
    final OwnerPropertyLocationsResponse response =
        OwnerPropertyLocationsResponse.fromJson({
          'results': [
            {
              'id': '704e0866-15d9-44ca-b0e6-0c846a00bc74',
              'name': 'Cairo',
              'slug': 'cairo',
              'created_at': '2026-08-29T16:55:02.808007+03:00',
              'updated_at': '2026-08-29T16:55:02.808007+03:00',
            },
          ],
        });

    expect(response.count, 1);
    expect(response.results, hasLength(1));
    expect(response.results.single.id, '704e0866-15d9-44ca-b0e6-0c846a00bc74');
    expect(response.results.single.name, 'Cairo');
    expect(response.results.single.slug, 'cairo');
  });

  test('builds a real multipart create-property payload', () {
    final List<File> photos = List<File>.generate(
      10,
      (index) => File('/tmp/property-photo-$index.jpg'),
    );
    final OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
        .copyWith(
          title: 'Cozy Studio',
          propertyType: 'استوديو',
          governorateId: 'cairo-governorate-id',
          governorate: 'القاهرة',
          districtId: 'nasr-city-id',
          district: 'مدينة نصر',
          street: 'شارع النصر',
          bedrooms: '1',
          bathrooms: '1',
          space: '65',
          floor: '3',
          location: const PropertyLocation(
            latitude: 30.0444,
            longitude: 31.2357,
          ),
          photoDrafts: photos
              .asMap()
              .entries
              .map(
                (entry) => OwnerPropertyPhotoDraft(
                  file: entry.value,
                  name: 'Photo ${entry.key + 1}',
                  description: 'Property photo ${entry.key + 1}',
                ),
              )
              .toList(growable: false),
          monthlyPrice: '7000',
          rentalDuration: '6',
          rentalUnit: 'شهر',
          amenities: {'واي فاي', 'جراج', 'مفروش'},
          description: 'A furnished studio near the metro station.',
          suitableFor: 'أفراد',
        );

    final Map<String, dynamic> body = form.toJson();

    expect(form.isBasicsReady, isTrue);
    expect(form.isPhotosReady, isFalse);
    expect(form.isPricingReady, isTrue);
    expect(body['property_type'], 'studio');
    expect(body['price_period'], 'monthly');
    expect(body['governorate'], 'cairo-governorate-id');
    expect(body['city'], 'nasr-city-id');
    expect(body['district'], 'شارع النصر');
    expect(body['latitude'], '30.044400');
    expect(body['longitude'], '31.235700');
    expect(body['suitable_for'], 'singles');
    expect(body['main_image'], same(photos.first));
    expect(body, isNot(contains('images')));
    expect(body, isNot(contains('video')));
    expect(body, isNot(contains('video_duration')));
    expect(body, isNot(contains('ownership_proof')));
    expect(body['has_wifi'], isTrue);
    expect(body['has_elevator'], isFalse);
    expect(
      jsonDecode(body['amenities'] as String),
      unorderedEquals(['wifi', 'garage']),
    );
    expect(OwnerAddPropertyContent.maxPhotoCount, 25);
    expect(
      OwnerAddPropertyContent.rentalUnitOptions,
      contains(LocaleKeys.ownerAddPropertyWeek),
    );
  });

  test('accepts blank optional metadata for every newly selected photo', () {
    final List<OwnerPropertyPhotoDraft> incomplete = List.generate(
      OwnerAddPropertyContent.minimumPhotoCount,
      (index) =>
          OwnerPropertyPhotoDraft(file: File('/tmp/new-photo-$index.jpg')),
    );
    final OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
        .copyWith(
          photoDrafts: incomplete,
          videoUrl: 'https://example.com/tour.mp4',
        );

    expect(form.isPhotosReady, isTrue);
    expect(
      form
          .copyWith(
            photoDrafts: incomplete
                .asMap()
                .entries
                .map(
                  (entry) => entry.value.copyWith(
                    name: 'Photo ${entry.key + 1}',
                    description: 'Description ${entry.key + 1}',
                  ),
                )
                .toList(growable: false),
          )
          .isPhotosReady,
      isTrue,
    );
  });

  test(
    'edit retains image IDs, clears captions, and preserves all returned terms and amenities',
    () {
      final property = PropertyDetailsModel.fromJson({
        ...repository._propertyDetailsJson('media-edit'),
        'amenities': ['wifi', 'garage', 'swimming_pool'],
        'video': 'https://example.com/tour.mp4',
        'video_duration': 45,
      });
      final seed = OwnerAddPropertyMapper.fromProperty(property).form;
      expect(seed.street, 'شارع النصر');
      expect(seed.neighborhood, 'مدينة نصر');
      expect(seed.country, 'Egypt');
      expect(seed.buildingYear, '2020');
      expect(seed.deposit, 'one_month');
      expect(seed.smokingAllowed, isFalse);
      expect(seed.ownershipProofUrl, property.ownershipProof);
      expect(seed.videoUrl, property.video);
      expect(seed.unsupportedAmenities, {'swimming_pool'});
      expect(seed.isPricingReady, isFalse);
      final photos = List<OwnerPropertyPhotoDraft>.of(seed.photoDrafts);
      photos[1] = photos[1].copyWith(name: '', description: '');
      photos.insert(0, photos.removeAt(1));
      final form = seed.copyWith(
        photoDrafts: photos,
        clearVideo: true,
        removeVideo: true,
        clearOwnershipProof: true,
        removeOwnershipProof: true,
        clearSmokingAllowed: true,
      );
      final body = form.toJson(isEditing: true);
      expect(form.isPhotosReady, isFalse);
      expect(body['main_image_id'], 'image-0');
      expect(body, isNot(contains('main_image')));
      expect(jsonDecode(body['retained_image_ids'] as String), [
        'image-0',
        'cover-id',
        ...List.generate(8, (index) => 'image-${index + 1}'),
      ]);
      expect((jsonDecode(body['images_metadata'] as String) as List).first, {
        'id': 'image-0',
        'name': '',
        'description': '',
      });
      expect(body['main_image_name'], '');
      expect(body['main_image_description'], '');
      expect(body['remove_video'], isTrue);
      expect(body['remove_ownership_proof'], isTrue);
      expect(body['smoking_allowed'], '');
      expect(
        jsonDecode(body['amenities'] as String),
        contains('swimming_pool'),
      );
      expect(body['is_furnished'], isTrue);
      expect(body['street'], 'شارع النصر');
      expect(body['district'], 'مدينة نصر');
      expect(
        form.copyWith(neighborhood: '').toJson(isEditing: true)['district'],
        '',
      );
    },
  );

  testWidgets('goes from photos to documented pricing fields', (tester) async {
    configurePhoneViewport(tester);
    final PropertyDetailsModel property = PropertyDetailsModel.fromJson({
      ...repository._propertyDetailsJson('video-flow-property'),
      'amenities': ['wifi', 'swimming_pool'],
    });

    await tester.pumpWidget(
      buildScreen(OwnerPropertyFlowScreen(property: property)),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('التالي — الصور'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    expect(find.byType(AddPropertyPricingPage), findsOneWidget);
    expect(
      tester
          .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
          .form
          .isPricingReady,
      isFalse,
    );
    final unavailableAmenity = find.text('Swimming pool');
    await tester.tap(find.text(LocaleKeys.ownerPropertyReviewAction));
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text(LocaleKeys.ownerAddPropertyAmenities), findsNWidgets(2));
    expect(find.byType(PropertyReviewSheet), findsNothing);
    await tester.ensureVisible(unavailableAmenity);
    await tester.tap(unavailableAmenity);
    await tester.pumpAndSettle();
    final updated = tester
        .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
        .form;
    expect(updated.unsupportedAmenities, isEmpty);
    expect(updated.isPricingReady, isTrue);
    expect(find.text('Swimming pool'), findsNothing);
    expect(
      find.text(LocaleKeys.ownerAddPropertyFemaleStudents),
      findsOneWidget,
    );
    final periods = tester.widget<DropdownButton<TenantFilterOption>>(
      find.byType(DropdownButton<TenantFilterOption>),
    );
    expect(periods.items!.map((item) => item.value!.value), [
      'daily',
      'weekly',
      'monthly',
      'yearly',
    ]);
    expect(
      find.text('${LocaleKeys.ownerAddPropertyMinimumRentalMonths} *'),
      findsOneWidget,
    );
    expect(find.text(LocaleKeys.ownerAddPropertyDeposit), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('review edit returns to basics and retains the full draft', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    final property = PropertyDetailsModel.fromJson(
      repository._propertyDetailsJson('review-property'),
    );
    await tester.pumpWidget(
      buildScreen(OwnerPropertyFlowScreen(property: property)),
    );
    await tester.pumpAndSettle();
    await openEditReview(tester);
    final before = tester
        .widget<PropertyReviewSheet>(find.byType(PropertyReviewSheet))
        .form;
    final edit = find.byTooltip(
      '${LocaleKeys.editData}: ${LocaleKeys.ownerPropertyReviewBasics}',
    );
    await tester.ensureVisible(edit);
    await tester.tap(edit);
    await tester.pumpAndSettle();
    expect(find.byType(PropertyReviewSheet), findsNothing);
    final titleField = find.byWidgetPredicate(
      (widget) =>
          widget is TextField && widget.controller?.text == before.title,
    );
    await tester.enterText(titleField, 'Updated listing title');
    await tester.pumpAndSettle();
    await openEditReview(tester);
    final after = tester
        .widget<PropertyReviewSheet>(find.byType(PropertyReviewSheet))
        .form;
    expect(after.title, 'Updated listing title');
    expect(after.photoDrafts, before.photoDrafts);
    expect(after.monthlyPrice, before.monthlyPrice);
    expect(after.amenities, before.amenities);
    expect(repository.updateRequestCount, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets('offers analytics, deletion, and editing for owned properties', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerPropertiesScreen(initialProperties: ownerPropertiesFixture()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('عقاراتي'), findsWidgets);
    expect(find.byType(OwnerPropertyCard), findsWidgets);
    await selectPropertyTab(tester, OwnerPropertyFilter.accepted);
    expect(find.text('شقة مفروشة — مدينة نصر'), findsOneWidget);
    expect(tester.takeException(), isNull);

    final Finder furnishedCard = find.byKey(
      const ValueKey('nasr-city-furnished'),
    );
    expect(
      find.descendant(of: furnishedCard, matching: find.text('إجراءات')),
      findsNothing,
    );
    expect(
      find.descendant(of: furnishedCard, matching: find.text('إحصاءات العقار')),
      findsOneWidget,
    );

    await tester.tap(
      find.descendant(of: furnishedCard, matching: find.text('تعديل')),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(repository.lastDetailsId, 'nasr-city-furnished');
    expect(find.byType(OwnerPropertyFlowScreen), findsOneWidget);
    expect(find.text('تعديل العقار'), findsOneWidget);

    await submitEditFlow(tester);
    expect(find.byType(OwnerPropertiesScreen), findsOneWidget);
    expect(repository.updateRequestCount, 1);
    expect(repository.lastUpdateBody?['governorate'], 'cairo-governorate-id');
    expect(repository.lastUpdateBody?['city'], 'cairo-city-id');
    expect(repository.lastUpdateBody?['district'], 'مدينة نصر');

    expect(tester.takeException(), isNull);
  });

  testWidgets('runs O-REJECT-01 edit and resubmit flow', (tester) async {
    configurePhoneViewport(tester);
    final OwnerPropertyContent rejected = ownerPropertiesFixture().first
        .copyWith(
          id: 'nasr-city-rejected',
          views: 0,
          visitRequests: 0,
          status: OwnerPropertyStatus.rejected,
        );

    await tester.pumpWidget(
      buildScreen(OwnerPropertiesScreen(initialProperties: [rejected])),
    );
    await tester.pumpAndSettle();

    await selectPropertyTab(tester, OwnerPropertyFilter.rejected);
    await tester.tap(
      find.descendant(
        of: find.byKey(const ValueKey('nasr-city-rejected')),
        matching: find.text(rejected.title),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerPropertyRejectionScreen), findsOneWidget);
    expect(find.text('تم رفض عقارك'), findsOneWidget);
    expect(
      find.text(
        'تفاصيل المراجعة غير متاحة حالياً. حدّث بيانات العقار وأرسله للمراجعة مرة أخرى.',
      ),
      findsOneWidget,
    );
    expect(find.text('الصور غير واضحة أو لا تعبر عن العقار'), findsNothing);
    expect(find.text('تواصل مع الدعم'), findsNothing);

    final Finder resubmitButton = find.text('تعديل وإعادة الإرسال');
    await tester.scrollUntilVisible(resubmitButton, 260);
    await tester.drag(find.byType(ListView), const Offset(0, -140));
    await tester.pumpAndSettle();
    await tester.tap(resubmitButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.byType(OwnerPropertyFlowScreen), findsOneWidget);
    expect(repository.lastDetailsId, 'nasr-city-rejected');
    await submitEditFlow(tester);

    expect(find.byType(OwnerPropertiesScreen), findsOneWidget);
    expect(find.byKey(const ValueKey('nasr-city-rejected')), findsNothing);
    await selectPropertyTab(tester, OwnerPropertyFilter.underReview);
    expect(find.byKey(const ValueKey('nasr-city-rejected')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'existing media captions, cover, location, and rental terms remain editable',
    (tester) async {
      configurePhoneViewport(tester);
      repository.detailsOverrides = {
        'video': 'https://example.com/old-tour.mp4',
        'video_duration': 35,
      };
      repository.saveResponseOverrides = {'title': 'Server-normalized listing'};
      final property = ownerPropertiesFixture().first;
      await tester.pumpWidget(
        buildScreen(OwnerPropertiesScreen(initialProperties: [property])),
      );
      await tester.pumpAndSettle();
      await selectPropertyTab(tester, OwnerPropertyFilter.accepted);
      await tester.tap(find.text(LocaleKeys.ownerPropertiesEdit));
      await tester.pumpAndSettle();
      final basics = tester.widget<AddPropertyBasicsPage>(
        find.byType(AddPropertyBasicsPage),
      );
      basics.streetController.text = 'Updated street';
      basics.onStreetChanged('Updated street');
      basics.floorController.clear();
      basics.onFloorChanged('');
      basics.onLocationSelected(
        const PropertyLocation(latitude: 30.0444, longitude: 31.2357),
      );
      await tester.pump();
      expect(
        tester
            .widget<AddPropertyBasicsPage>(find.byType(AddPropertyBasicsPage))
            .form
            .isBasicsReady,
        isTrue,
      );
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyNextPhotos));
      await tester.pumpAndSettle();
      final photos = tester.widget<AddPropertyPhotosPage>(
        find.byType(AddPropertyPhotosPage),
      );
      expect(photos.form.videoUrl, 'https://example.com/old-tour.mp4');
      photos.onPhotoNameChanged(1, 'Garden bedroom');
      photos.onPhotoDescriptionChanged(1, 'Overlooks the garden');
      photos.onMainPhotoSelected(1);
      photos.onVideoRemoved();
      await tester.pump();
      expect(
        tester
            .widget<AddPropertyPhotosPage>(find.byType(AddPropertyPhotosPage))
            .isReady,
        isFalse,
      );
      photos.onVideoSelected(File('/tmp/replacement-tour.mp4'), 45);
      await tester.pump();
      await tester.tap(find.text(LocaleKeys.ownerAddPropertyPricingTitle).last);
      await tester.pumpAndSettle();
      final pricing = tester.widget<AddPropertyPricingPage>(
        find.byType(AddPropertyPricingPage),
      );
      pricing.onAdditionalDetailsChanged(
        pricing.form.copyWith(
          country: 'Egypt',
          neighborhood: 'New district',
          buildingYear: '2018',
          deposit: '5000',
          areaDescription: '120 m² of usable space',
          clearSmokingAllowed: true,
          clearOwnershipProof: true,
          removeOwnershipProof: true,
        ),
      );
      await tester.pump();
      await tester.tap(find.text(LocaleKeys.ownerPropertyReviewAction));
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.ownerPropertiesSaveChanges));
      await tester.pumpAndSettle();
      expect(find.byType(PropertyEditReviewSheet), findsOneWidget);
      final body = repository.lastUpdateBody!;
      expect(repository.updateRequestCount, 1);
      expect(repository.imageRequests, isEmpty);
      expect(body['main_image_id'], 'image-0');
      expect(body['main_image_name'], 'Garden bedroom');
      expect(body['main_image_description'], 'Overlooks the garden');
      expect((jsonDecode(body['images_metadata'] as String) as List).first, {
        'id': 'image-0',
        'name': 'Garden bedroom',
        'description': 'Overlooks the garden',
      });
      expect(body['street'], 'Updated street');
      expect(body['floor'], '');
      expect(body['area'], 120);
      expect(body['space'], '120 m² of usable space');
      expect(body['district'], 'New district');
      expect(body['country'], 'Egypt');
      expect(body['building_year'], '2018');
      expect(body['deposit'], '5000');
      expect(body['smoking_allowed'], '');
      expect(body.containsKey('remove_video'), isFalse);
      expect(body['video'], isA<File>());
      expect(body['video_duration'], 45);
      expect(body['remove_ownership_proof'], isTrue);
      await tester.tap(find.text(LocaleKeys.ownerPropertyEditReviewDone));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('Server-normalized listing'), findsNothing);
      await selectPropertyTab(tester, OwnerPropertyFilter.underReview);
      expect(find.text('Server-normalized listing'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'delete confirmation supports cancel, failure, and a successful retry',
    (tester) async {
      configurePhoneViewport(tester);
      final property = ownerPropertiesFixture().first;
      await tester.pumpWidget(
        buildScreen(OwnerPropertiesScreen(initialProperties: [property])),
      );
      await tester.pumpAndSettle();
      await selectPropertyTab(tester, OwnerPropertyFilter.accepted);

      Future<void> openDeleteSheet() async {
        final delete = find.text(LocaleKeys.ownerPropertiesDeleteProperty);
        await tester.ensureVisible(delete);
        await tester.tap(delete);
        await tester.pumpAndSettle();
        expect(find.byType(OwnerPropertyDeleteSheet), findsOneWidget);
      }

      await openDeleteSheet();
      await tester.tap(find.text(LocaleKeys.cancel));
      await tester.pumpAndSettle();
      expect(repository.deleteRequests, isEmpty);
      expect(find.byKey(ValueKey(property.id)), findsOneWidget);

      await openDeleteSheet();
      await tester.tap(find.text(LocaleKeys.ownerPropertiesDelete));
      await tester.pump();
      expect(repository.deleteRequests, hasLength(1));
      expect(
        repository.deleteRequests.single.api,
        ApiConstants.deleteProperty(property.id),
      );
      expect(
        repository.deleteRequests.single.httpRequestType,
        HttpRequestType.delete,
      );
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
      expect(
        tester
            .widget<TextButton>(
              find.widgetWithText(TextButton, LocaleKeys.cancel),
            )
            .onPressed,
        isNull,
      );
      repository.deleteResponses.first.complete(false);
      await tester.pumpAndSettle();
      expect(find.byType(OwnerPropertyDeleteSheet), findsOneWidget);
      expect(find.byKey(ValueKey(property.id)), findsOneWidget);
      expect(
        find.text(
          'Cannot delete property with active or upcoming visit requests.',
        ),
        findsOneWidget,
      );

      await tester.tap(find.text(LocaleKeys.ownerPropertiesDelete));
      await tester.pump();
      expect(repository.deleteRequests, hasLength(2));
      repository.deleteResponses.last.complete(true);
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.byType(OwnerPropertyDeleteSheet), findsNothing);
      expect(find.byKey(ValueKey(property.id)), findsNothing);
      expect(find.text('Server deleted the property'), findsOneWidget);
      toastification.dismissAll(delayForAnimation: false);
      await tester.pump(const Duration(seconds: 1));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('connects add property from O-PROPS-01b', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerPropertiesScreen(initialProperties: ownerPropertiesFixture()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('إضافة عقار'));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerPropertyFlowScreen), findsOneWidget);
    expect(find.text('إضافة عقار جديد'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _OwnerPropertiesRepository implements BaseRepository {
  String? lastDetailsId;
  Map<String, dynamic>? lastUpdateBody;
  int updateRequestCount = 0;
  Completer<bool>? createResponse;
  final List<CrudBaseParmas> createRequests = [];
  final List<CrudBaseParmas> imageRequests = [];
  final List<Completer<bool>> imageResponses = [];
  final List<CrudBaseParmas> deleteRequests = [];
  final List<Completer<bool>> deleteResponses = [];
  Map<String, dynamic> detailsOverrides = {};
  Map<String, dynamic> saveResponseOverrides = {};

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.api == ApiConstants.propertyFilterOptions) {
      return Success(
        BaseModel<T>(
          key: '',
          msg: '',
          data: params.mapper!({
            'price_periods': [
              {'value': 'monthly', 'label': 'شهر'},
              {'value': 'daily', 'label': 'يوم'},
              {'value': 'weekly', 'label': 'أسبوع'},
              {'value': 'yearly', 'label': 'سنة'},
            ],
            'suitable_for': [
              {'value': 'families', 'label': 'عائلات'},
              {'value': 'students', 'label': 'طلاب'},
            ],
            'amenities': [
              {
                'value': 'wifi',
                'label': 'واي فاي',
                'query_parameter': 'has_wifi',
              },
              {'value': 'swimming_pool', 'label': 'Swimming pool'},
            ],
          }),
        ),
      );
    }
    if (params.api == ApiConstants.propertyTypes) {
      return Success(
        BaseModel<T>(
          key: '',
          msg: '',
          data: params.mapper!({
            'count': 1,
            'results': [
              {'id': 'apartment-type', 'name': 'شقة', 'slug': 'apartment'},
            ],
          }),
        ),
      );
    }
    if (params.api == ApiConstants.createProperty) {
      createRequests.add(params);
      if (!await createResponse!.future) {
        return const Error(ServerFailure('Creation failed'));
      }
      return Success(
        BaseModel(
          key: '',
          msg: '',
          data: params.mapper!(
            _savedPropertyJson(
              'created-property',
              params.body!,
              isCreating: true,
            ),
          ),
        ),
      );
    }
    if (params.api.endsWith('/images/')) {
      imageRequests.add(params);
      final int index = imageRequests.length;
      final Completer<bool> response = Completer<bool>();
      imageResponses.add(response);
      if (!await response.future) {
        return const Error(ServerFailure('Image upload failed'));
      }
      return Success(
        BaseModel(
          key: '',
          msg: '',
          data: params.mapper!({
            'id': 'uploaded-$index',
            'image': 'https://example.com/uploaded-$index.jpg',
            'name': params.body!['name'],
            'description': params.body!['description'],
            'created_at': '2026-07-26T22:12:45.392372+03:00',
            'updated_at': '2026-07-26T22:12:45.392430+03:00',
          }),
        ),
      );
    }
    if (params.api.endsWith('/delete/')) {
      deleteRequests.add(params);
      final response = Completer<bool>();
      deleteResponses.add(response);
      if (!await response.future) {
        return const Error(
          ServerFailure(
            'Cannot delete property with active or upcoming visit requests.',
          ),
        );
      }
      return Success(
        BaseModel<T>(
          key: '',
          msg: 'Server deleted the property',
          data: params.mapper!({
            'id': params.api.split('/')[1],
            'deleted': true,
          }),
        ),
      );
    }
    final List<String> pathSegments = params.api
        .split('/')
        .where((segment) => segment.isNotEmpty)
        .toList(growable: false);
    final String propertyId = pathSegments.length > 1
        ? pathSegments[1]
        : 'property-id';
    if (params.httpRequestType == HttpRequestType.get) {
      lastDetailsId = propertyId;
    } else if (params.httpRequestType == HttpRequestType.patch) {
      updateRequestCount++;
      lastUpdateBody = params.body;
    }
    final T data = params.mapper!(
      params.httpRequestType == HttpRequestType.patch
          ? _savedPropertyJson(propertyId, params.body!)
          : _propertyDetailsJson(propertyId),
    );
    return Success(
      BaseModel<T>(
        key: '',
        msg: params.httpRequestType == HttpRequestType.patch
            ? 'Server saved the property changes'
            : '',
        data: data,
      ),
    );
  }

  Map<String, dynamic> _propertyDetailsJson(String propertyId) {
    return {
      'id': propertyId,
      'owner': {'id': 'owner-id', 'full_name': 'Ahmed', 'avatar': ''},
      'main_image': 'https://example.com/main.jpg',
      'main_image_id': 'cover-id',
      'title': 'شقة مفروشة — مدينة نصر',
      'description': 'شقة مفروشة بإضاءة طبيعية ومرافق متكاملة',
      'price': '6500',
      'price_period': 'monthly',
      'property_type': 'apartment',
      'is_furnished': true,
      'bedrooms': 2,
      'bathrooms': 1,
      'area': 120,
      'space': '120',
      'floor': 3,
      'rental_period': 6,
      'suitable_for': 'singles',
      'smoking_allowed': false,
      'country': 'Egypt',
      'city': {
        'id': 'cairo-city-id',
        'name': 'القاهرة',
        'slug': 'cairo',
        'governorate': 'cairo-governorate-id',
        'governorate_name': 'القاهرة',
      },
      'district': 'مدينة نصر',
      'street': 'شارع النصر',
      'building_year': 2020,
      'deposit': 'one_month',
      'ownership_proof': 'https://example.com/ownership-proof.jpg',
      'video': 'https://example.com/tour.mp4',
      'video_duration': 45,
      'latitude': '30.0444',
      'longitude': '31.2357',
      'amenities': ['wifi', 'garage'],
      'images': [
        {
          'id': 'cover-id',
          'image': 'https://example.com/main.jpg',
          'name': '',
          'description': '',
        },
        ...List<Map<String, dynamic>>.generate(
          9,
          (index) => {
            'id': 'image-$index',
            'image': 'https://example.com/property-$index.jpg',
            'name': 'image-$index',
            'description': '',
            'created_at': '',
            'updated_at': '',
          },
        ),
      ],
      ...detailsOverrides,
    };
  }

  Map<String, dynamic> _savedPropertyJson(
    String propertyId,
    Map<String, dynamic> body, {
    bool isCreating = false,
  }) {
    final json = _propertyDetailsJson(propertyId);
    for (final field in [
      'title',
      'description',
      'price_period',
      'property_type',
      'is_furnished',
      'bedrooms',
      'bathrooms',
      'area',
      'space',
      'rental_period',
      'suitable_for',
      'country',
      'district',
      'street',
      'latitude',
      'longitude',
      'deposit',
    ]) {
      if (body.containsKey(field)) json[field] = body[field];
    }
    json['price'] = double.parse(body['price'] as String).toStringAsFixed(2);
    for (final field in ['floor', 'building_year', 'smoking_allowed']) {
      json[field] = body[field] == '' ? null : body[field];
    }
    json['amenities'] = jsonDecode(body['amenities'] as String);
    json['status'] = 'under_review';
    json['is_verified'] = false;
    json['updated_at'] = '2026-10-05T12:00:00+03:00';
    final retained = isCreating
        ? <dynamic>[]
        : jsonDecode(body['retained_image_ids'] as String) as List;
    final metadata = isCreating
        ? <dynamic>[]
        : jsonDecode(body['images_metadata'] as String) as List;
    final images = <Map<String, dynamic>>[
      for (final id in retained)
        {
          ...(json['images'] as List).cast<Map<String, dynamic>>().firstWhere(
            (image) => image['id'] == id,
          ),
          ...metadata.cast<Map<String, dynamic>>().firstWhere(
            (image) => image['id'] == id,
          ),
        },
    ];
    if (body['main_image'] is File) {
      images.insert(0, {
        'id': isCreating ? 'created-cover' : 'replaced-cover',
        'image': 'https://example.com/cover.jpg',
        'name': body['main_image_name'],
        'description': body['main_image_description'],
      });
    } else {
      final index = images.indexWhere(
        (image) => image['id'] == body['main_image_id'],
      );
      images.insert(0, images.removeAt(index));
      images.first.addAll({
        'name': body['main_image_name'],
        'description': body['main_image_description'],
      });
    }
    json.addAll({
      'main_image_id': images.first['id'],
      'main_image': images.first['image'],
      'main_image_name': images.first['name'],
      'main_image_description': images.first['description'],
      'images': images,
    });
    if (isCreating || body['remove_video'] == true) {
      json['video'] = null;
      json['video_duration'] = null;
    }
    if (body['video'] is File) {
      json['video'] = 'https://example.com/tour.mp4';
      json['video_duration'] = body['video_duration'];
    }
    if (isCreating || body['remove_ownership_proof'] == true) {
      json['ownership_proof'] = null;
      json['is_ownership_verified'] = false;
    }
    return {...json, ...saveResponseOverrides};
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _OwnerPropertiesAssetLoader extends AssetLoader {
  const _OwnerPropertiesAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      ...jsonDecode(
            File(
              '../../packages/core/assets/translations/ar.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>,
      'home': 'الرئيسية',
      'chats': 'الشات',
      'search': 'بحث',
      'notifications_owner_properties_navigation': 'عقاراتي',
      'notifications_owner_requests_navigation': 'الطلبات',
      'notifications_owner_more_navigation': 'المزيد',
      'owner_properties_title': 'عقاراتي',
      'owner_properties_add': 'إضافة عقار',
      'owner_properties_edit': 'تعديل',
      'owner_properties_analytics': 'إحصاءات',
      'owner_properties_actions': 'إجراءات',
      'owner_properties_options': 'خيارات العقار',
      'owner_properties_edit_property': 'تعديل العقار',
      'owner_properties_pause': 'إيقاف مؤقت',
      'owner_properties_reactivate': 'إعادة تفعيل العقار',
      'owner_properties_mark_rented': 'وضع علامة مؤجّر',
      'owner_properties_delete_property': 'حذف العقار',
      'owner_properties_price_unit': 'ج/شهر',
      'owner_properties_view_unit': 'مشاهدة',
      'owner_properties_visit_unit': 'زيارة',
      'owner_property_status_verified': 'موثّق',
      'owner_property_status_pending': 'قيد المراجعة',
      'owner_property_status_accepted': 'مقبول',
      'owner_property_status_hidden': 'مخفي',
      'owner_property_status_rejected': 'مرفوض',
      'owner_property_status_rented': 'مؤجّر',
      'owner_properties_saved': 'تم حفظ تعديلات العقار',
      'owner_properties_resubmitted': 'تمت إعادة إرسال العقار للمراجعة',
      'owner_properties_paused_message': 'تم إيقاف العقار مؤقتاً',
      'owner_properties_reactivated_message': 'تمت إعادة تفعيل العقار',
      'owner_properties_marked_rented_message': 'تم وضع علامة مؤجّر على العقار',
      'owner_properties_deleted_message': 'تم حذف العقار',
      'owner_properties_edit_title': 'تعديل العقار',
      'owner_properties_delete': 'حذف',
      'owner_properties_photos': 'صور العقار',
      'owner_properties_photo_unit': 'صورة',
      'owner_properties_add_photo': 'إضافة',
      'owner_properties_name': 'اسم العقار',
      'owner_properties_name_required': 'أدخل اسم العقار',
      'owner_properties_monthly_price': 'السعر الشهري',
      'owner_properties_bedrooms': 'عدد الغرف',
      'owner_properties_area': 'المساحة',
      'owner_properties_description': 'الوصف',
      'owner_properties_currency': 'جنيه',
      'owner_properties_square_meter': 'م²',
      'owner_properties_save_changes': 'حفظ التعديلات',
      'owner_properties_preview': 'معاينة العقار',
      'owner_add_property_title': 'إضافة عقار جديد',
      'owner_add_property_basics_progress': 'الخطوة 1 من 5 — معلومات العقار',
      'owner_add_property_next_photos': 'التالي — الصور',
      'owner_add_property_type': 'نوع العقار',
      'owner_add_property_name_section': 'عنوان العقار',
      'owner_add_property_title_label': 'العنوان',
      'owner_add_property_title_example': 'مثال: شقة مفروشة قريبة من المترو',
      'owner_add_property_title_hint': 'اكتب عنواناً واضحاً للعقار',
      'owner_add_property_bedrooms': 'عدد الغرف',
      'owner_add_property_bathrooms': 'عدد الحمامات',
      'owner_add_property_space': 'المساحة (م²)',
      'owner_add_property_floor': 'الدور',
      'owner_add_property_floor_hint': 'اختياري: 0 للأرضي، و-1 للبدروم',
      'owner_add_property_area_description': 'وصف المساحة',
      'owner_add_property_minimum_rental_months': 'أقل مدة إيجار (بالشهور)',
      'owner_add_property_price_period': 'فترة السعر',
      'owner_add_property_price_summary': '{price} ج.م / {unit}',
      'owner_add_property_students': 'طلاب',
      'owner_add_property_female_students': 'طالبات',
      'owner_add_property_building_year': 'سنة البناء',
      'owner_add_property_details': 'تفاصيل العقار',
      'owner_add_property_map_title': 'موقع العقار على الخريطة',
      'owner_add_property_map_subtitle':
          'حدد موقع العقار بدقة عشان نراجع الإعلان بشكل أسرع',
      'owner_add_property_map_search': 'ابحث عن الموقع...',
      'owner_add_property_location_selected': 'تم تحديد الموقع',
      'owner_add_property_select_location': 'تحديد الموقع',
      'owner_add_property_selected_location': 'الموقع المحدد',
      'owner_add_property_location_privacy':
          'قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية',
      'owner_add_property_address_section': 'المنطقة والعنوان',
      'owner_add_property_choose': 'اختر',
      'owner_add_property_governorate': 'المحافظة',
      'owner_add_property_city': 'المدينة',
      'owner_add_property_street': 'الشارع',
      'owner_add_property_street_hint': 'اكتب اسم الشارع',
      'owner_add_property_extra_progress': 'الخطوة 5 من 5 — التفاصيل الإضافية',
      'owner_add_property_submitting': 'جار الإرسال...',
      'owner_add_property_submit_review': 'إرسال للمراجعة',
      'owner_add_property_smoking_question': 'التدخين مسموح؟',
      'owner_add_property_suitable_for': 'العقار مناسب لـ',
      'owner_add_property_proof_title': 'إثبات ملكية العقار',
      'owner_add_property_proof_subtitle':
          'ممكن ترفع وصل كهربا، وصل مياه، أو عقد الملكية',
      'owner_add_property_proof_upload': 'ارفع إثبات الملكية',
      'owner_add_property_proof_change': 'اضغط لتغيير المستند',
      'owner_add_property_proof_formats': 'JPG · PNG',
      'owner_add_property_proof_attached': 'تم إرفاق المستند للمراجعة',
      'owner_add_property_proof_internal': 'المستند ده للمراجعة الداخلية فقط',
      'owner_add_property_proof_private': 'مش هيظهر للمستخدمين أو المستأجرين',
      'owner_add_property_proof_private_continuation':
          'ومش هيظهر للمستخدمين أو المستأجرين',
      'owner_add_property_photos_progress': 'الخطوة 2 من 5 — صور العقار',
      'owner_add_property_next_video': 'التالي — فيديو العقار',
      'owner_add_property_photos_ready': 'الصور جاهزة للمراجعة',
      'owner_add_property_photos_ready_description':
          'تقدر تضيف صور زيادة أو تكمل لخطوة الفيديو',
      'owner_add_property_photos_remaining':
          'اضغط على مربعات الإضافة لرفع {count} صور كمان',
      'owner_add_property_photos_count':
          '{count} / {minimum} صور مرفوعة (الحد الأدنى {minimum})',
      'owner_add_property_photo_tips': 'نصائح للصور',
      'owner_add_property_photo_tip_rooms':
          'صوّر كل الغرف: صالة، غرف نوم، مطبخ، حمام',
      'owner_add_property_photo_tip_lighting': 'استخدم إضاءة طبيعية',
      'owner_add_property_photo_tip_privacy':
          'تأكد من خلو الصور من أي أرقام هواتف أو معلومات شخصية',
      'owner_add_property_photo_tip_limits':
          'الحد الأدنى 10 صور، وتقدر ترفع لحد 25 صورة',
      'owner_add_property_pricing_title': 'التسعير والتفاصيل',
      'owner_add_property_pricing_progress': 'الخطوة 4 من 5 — السعر والتفاصيل',
      'owner_add_property_next_extra': 'التالي — التفاصيل الإضافية',
      'owner_add_property_amenities': 'المرافق والخدمات',
      'owner_add_property_pricing_ready':
          'بيانات التسعير والوصف جاهزة للمتابعة',
      'owner_add_property_pricing_required':
          'اكتب سعر، مدة إيجار، ووصف واضح لا يقل عن 10 أحرف',
      'owner_add_property_price': 'السعر',
      'egyptian_pound_short': 'ج.م',
      'owner_add_property_currency': 'ج.م',
      'owner_add_property_deposit': 'تأمين الشقة',
      'owner_add_property_rental_period': 'فترة التأجير',
      'owner_add_property_count': 'العدد',
      'owner_add_property_unit': 'الوحدة',
      'owner_add_property_rental_summary': 'أقل مدة إيجار: {count} شهور',
      'owner_add_property_description': 'وصف العقار',
      'owner_add_property_description_label': 'الوصف',
      'owner_add_property_description_hint': 'اكتب وصفاً جذاباً للعقار…',
      'owner_add_property_apartment': 'شقة',
      'owner_add_property_room': 'غرفة',
      'owner_add_property_studio': 'استوديو',
      'owner_add_property_villa': 'فيلا',
      'owner_add_property_whole_floor': 'دور',
      'owner_add_property_roof': 'روف',
      'owner_add_property_no_deposit': 'بدون تأمين',
      'owner_add_property_half_month': 'نصف شهر',
      'owner_add_property_one_month': 'شهر واحد',
      'owner_add_property_two_months': 'شهرين',
      'owner_add_property_day': 'يوم',
      'owner_add_property_week': 'أسبوع',
      'owner_add_property_month': 'شهر',
      'owner_add_property_year': 'سنة',
      'owner_add_property_wifi': 'واي فاي',
      'owner_add_property_furnished': 'مفروش',
      'owner_add_property_garage': 'جراج',
      'owner_add_property_elevator': 'أسانسير',
      'owner_add_property_security': 'أمن',
      'owner_add_property_balcony': 'بلكونة',
      'owner_add_property_air_conditioning': 'تكييف',
      'owner_add_property_natural_gas': 'غاز طبيعي',
      'owner_add_property_electricity_meter': 'عداد كهرباء',
      'owner_add_property_water_meter': 'عداد مياه',
      'owner_add_property_near_metro': 'قريب من المترو',
      'owner_add_property_allowed': 'مسموح',
      'owner_add_property_not_allowed': 'ممنوع',
      'owner_add_property_by_agreement': 'حسب الاتفاق',
      'owner_add_property_everyone': 'الكل',
      'owner_add_property_males_only': 'ولاد فقط',
      'owner_add_property_females_only': 'بنات فقط',
      'owner_add_property_families': 'عائلات',
      'owner_add_property_individuals': 'أفراد',
      'owner_add_property_shared': 'مشاركة',
      'owner_add_property_area_summary': 'المنطقة',
      'owner_add_property_photos_summary': 'الصور',
      'owner_add_property_video_summary': 'الفيديو',
      'owner_add_property_proof_summary': 'إثبات الملكية',
      'owner_add_property_submitted_at_summary': 'وقت الإرسال',
      'owner_add_property_monthly_price': '{price} ج.م/شهر',
      'owner_add_property_photo_count_summary': '{count} صورة',
      'owner_add_property_video_skipped': 'تم تخطي الفيديو',
      'owner_add_property_video_uploaded_summary':
          'تم رفع الفيديو ({duration})',
      'owner_add_property_today_at': 'اليوم {time} {period}',
      'owner_add_property_am': 'ص',
      'owner_add_property_pm': 'م',
      'owner_property_video_title': 'فيديو العقار',
      'owner_property_video_subtitle': 'صوّر فيديو قصير يوضح العقار للمستأجرين',
      'owner_property_video_step_progress': 'الخطوة 3 من 5 — فيديو العقار',
      'owner_property_video_requirements': 'متطلبات الفيديو',
      'owner_property_video_requirement_duration':
          'مدة الفيديو لا تزيد عن دقيقة واحدة (60 ثانية)',
      'owner_property_video_requirement_rooms':
          'صوّر مدخل العقار والغرف الأساسية',
      'owner_property_video_requirement_stable': 'خلي الفيديو واضح وثابت',
      'owner_property_video_requirement_privacy':
          'متظهرش أرقام تليفونات أو مستندات شخصية في الفيديو',
      'owner_property_video_maximum_duration': 'الحد الأقصى: 60 ثانية',
      'owner_property_video_upload_or_record': 'ارفع أو صوّر فيديو للعقار',
      'owner_property_video_record': 'تصوير فيديو',
      'owner_property_video_upload': 'رفع فيديو',
      'owner_property_video_preparing': 'جاري تجهيز الفيديو…',
      'owner_property_video_uploaded': 'تم الرفع',
      'owner_property_video_change': 'تغيير الفيديو',
      'owner_property_video_remove': 'حذف الفيديو',
      'owner_property_video_too_long': 'الفيديو لازم يكون أقل من دقيقة',
      'owner_property_video_failed': 'فشل رفع الفيديو، حاول تاني',
      'owner_property_video_privacy_hint':
          'الفيديو هيظهر للمستأجرين بعد مراجعة سكون، '
          'فمتظهرش فيه أي بيانات شخصية',
      'owner_property_video_skip': 'تخطي الفيديو',
      'owner_property_video_next_pricing': 'التالي — التسعير',
      'owner_property_nasr_city_title': 'شقة مفروشة — مدينة نصر',
      'owner_property_nasr_city_location': 'مدينة نصر، القاهرة',
      'owner_property_nasr_city_description':
          'شقة مفروشة بإضاءة طبيعية ومرافق متكاملة',
      'owner_property_studio_title': 'ستوديو — التجمع الخامس',
      'owner_property_studio_location': 'التجمع الخامس، القاهرة',
      'owner_property_studio_description':
          'ستوديو حديث قريب من الخدمات والمواصلات',
      'owner_property_mohandessin_title': 'شقة 3 غرف — المهندسين',
      'owner_property_mohandessin_location': 'المهندسين، الجيزة',
      'owner_property_mohandessin_description':
          'شقة واسعة من ثلاث غرف بإطلالة هادئة',
      'owner_property_rejection_title': 'سبب الرفض',
      'owner_property_rejected_headline': 'تم رفض عقارك',
      'owner_property_rejection_details_unavailable':
          'تفاصيل المراجعة غير متاحة حالياً. حدّث بيانات العقار وأرسله للمراجعة مرة أخرى.',
      'owner_property_rejection_reasons': 'أسباب الرفض',
      'owner_property_reason_unclear_photos':
          'الصور غير واضحة أو لا تعبر عن العقار',
      'owner_property_reason_incomplete_info': 'المعلومات المدخلة غير مكتملة',
      'owner_property_reviewer_notes': 'ملاحظات المراجع',
      'owner_property_reviewer_notes_description':
          'يرجى إعادة تصوير غرف النوم والمطبخ بإضاءة أوضح. '
          'أضف أيضاً عدد الطوابق وسنة البناء.',
      'owner_property_rejection_warning':
          'العقار لن يظهر في البحث حتى تُصحح البيانات وتُعيد الإرسال',
      'owner_property_edit_and_resubmit': 'تعديل وإعادة الإرسال',
      'owner_property_contact_support': 'تواصل مع الدعم',
      'owner_analytics_title': 'إحصاءات العقار',
      'owner_analytics_thirty_days': '30 يوم',
      'owner_analytics_views': 'المشاهدات',
      'owner_analytics_visit_requests': 'طلبات الزيارة',
      'owner_analytics_saved': 'الحفظ',
      'owner_analytics_acceptance_rate': 'نسبة القبول',
      'owner_analytics_views_last_fourteen_days': 'المشاهدات خلال آخر 14 يوم',
      'owner_analytics_fourteen_days_ago': 'منذ 14 يوم',
      'owner_analytics_today': 'اليوم',
      'owner_analytics_top_interests': 'أهم اهتمامات الزوار',
      'owner_analytics_interest_area': 'المساحة',
      'owner_analytics_interest_price': 'السعر',
      'owner_analytics_interest_location': 'الموقع',
      'owner_analytics_interest_amenities': 'المرافق',
      'owner_analytics_open_revenue': 'عرض الإيرادات',
      'owner_revenue_title': 'الإيرادات',
      'owner_revenue_this_month': 'إجمالي هذا الشهر',
      'owner_revenue_currency': 'ج',
      'owner_revenue_growth': '↑ 8% عن الشهر السابق',
      'owner_revenue_properties': 'إيرادات العقارات',
      'owner_revenue_latest_transactions': 'أحدث المعاملات',
      'owner_revenue_paid': 'مدفوع',
      'owner_revenue_due': 'مستحق',
      'owner_revenue_late': 'متأخر',
      'owner_revenue_paid_this_month': 'تم الدفع هذا الشهر',
      'owner_revenue_due_june_fifteen': 'مستحق 15 يونيو',
      'owner_revenue_late_since_june_one': 'متأخر منذ 1 يونيو',
      'owner_revenue_zamalek_room': 'غرفة — الزمالك',
      'owner_revenue_nasr_monthly_rent': 'إيجار شهر مدينة نصر',
      'owner_revenue_mohandessin_rent': 'إيجار المهندسين',
      'owner_revenue_platform_fee': 'رسوم المنصة',
      'owner_revenue_june_one': '1 يونيو',
      'owner_revenue_may_twenty_eight': '28 مايو',
    };
  }
}
