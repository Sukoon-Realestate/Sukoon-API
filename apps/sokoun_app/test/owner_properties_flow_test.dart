import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_add_property_flow_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_video_page.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/shared_widgets/retry_view.dart';

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
        icon: Icons.apartment_rounded,
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
        icon: Icons.meeting_room_outlined,
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
        icon: Icons.home_work_outlined,
      ),
    ];
  }

  Future<void> submitEditFlow(WidgetTester tester) async {
    await tester.tap(find.text('التالي — الصور'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('التالي — فيديو العقار'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تخطي الفيديو'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('التالي — التفاصيل الإضافية'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('حفظ التعديلات'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
  }

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
    final File ownershipProof = File('/tmp/ownership-proof.png');
    final File video = File('/tmp/property-video.mp4');
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
          buildingYear: '2020',
          mapQuery: 'مدينة نصر، القاهرة',
          isLocationSelected: true,
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
          video: OwnerPropertyVideoSelection(
            file: video,
            duration: const Duration(seconds: 45),
          ),
          monthlyPrice: '7000',
          deposit: 'شهر واحد',
          rentalDuration: '6',
          rentalUnit: 'شهر',
          amenities: {'واي فاي', 'جراج', 'مفروش'},
          description: 'A furnished studio near the metro station.',
          smokingPolicy: 'ممنوع',
          suitableFor: 'أفراد',
          ownershipProof: ownershipProof,
        );

    final Map<String, dynamic> body = form.toRequestBody();

    expect(form.isBasicsReady, isTrue);
    expect(form.isPhotosReady, isTrue);
    expect(form.isPricingReady, isTrue);
    expect(form.isExtraDetailsReady, isTrue);
    expect(body['property_type'], 'studio');
    expect(body['price_period'], 'monthly');
    expect(body['governorate'], 'cairo-governorate-id');
    expect(body['city'], 'nasr-city-id');
    expect(body['district'], 'nasr-city-id');
    expect(body['main_image'], same(photos.first));
    expect(body['images'], hasLength(9));
    expect(body['video'], same(video));
    expect(body['video_duration'], 45);
    expect(body['ownership_proof'], same(ownershipProof));
    expect(body['has_wifi'], isTrue);
    expect(body['has_elevator'], isFalse);
    expect(OwnerAddPropertyContent.maxPhotoCount, 25);
    expect(OwnerAddPropertyContent.rentalUnitOptions, isNot(contains('أسبوع')));
  });

  test('requires metadata for every newly selected photo', () {
    final List<OwnerPropertyPhotoDraft> incomplete = List.generate(
      OwnerAddPropertyContent.minimumPhotoCount,
      (index) =>
          OwnerPropertyPhotoDraft(file: File('/tmp/new-photo-$index.jpg')),
    );
    final OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
        .copyWith(photoDrafts: incomplete);

    expect(form.isPhotosReady, isFalse);
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

  testWidgets('retry view invokes its recoverable request', (tester) async {
    configurePhoneViewport(tester);
    int retryCount = 0;

    await tester.pumpWidget(
      buildScreen(
        Scaffold(
          body: AppRetryView(
            onRetry: () async {
              retryCount++;
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('app-retry-button')));
    await tester.pumpAndSettle();

    expect(retryCount, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('places O-ADD-02V after the photos step', (tester) async {
    configurePhoneViewport(tester);
    final PropertyDetailsModel property = PropertyDetailsModel.fromJson(
      repository._propertyDetailsJson('video-flow-property'),
    );

    await tester.pumpWidget(
      buildScreen(OwnerPropertyFlowScreen(property: property)),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('التالي — الصور'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('التالي — فيديو العقار'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    expect(find.byType(AddPropertyVideoPage), findsOneWidget);
    expect(find.text('فيديو العقار'), findsWidgets);
    expect(find.text('تخطي الفيديو'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('keeps only API-backed property actions available', (
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
    expect(find.byType(OwnerPropertyCard), findsNWidgets(3));
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
      find.descendant(of: furnishedCard, matching: find.text('إحصاءات')),
      findsNothing,
    );

    await tester.tap(
      find.descendant(of: furnishedCard, matching: find.text('تعديل')),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(repository.lastDetailsId, 'nasr-city-furnished');
    expect(find.byType(OwnerEditPropertyScreen), findsOneWidget);
    expect(find.text('تعديل العقار'), findsOneWidget);

    await submitEditFlow(tester);
    expect(find.byType(OwnerPropertiesScreen), findsOneWidget);
    expect(find.text('تم حفظ تعديلات العقار'), findsOneWidget);
    expect(repository.updateRequestCount, 1);
    expect(repository.lastUpdateBody?['governorate'], 'cairo-governorate-id');
    expect(repository.lastUpdateBody?['city'], 'cairo-city-id');
    expect(repository.lastUpdateBody?['district'], 'cairo-city-id');

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

    await tester.tap(find.byKey(const ValueKey('nasr-city-rejected')));
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

    expect(find.byType(OwnerEditPropertyScreen), findsOneWidget);
    expect(repository.lastDetailsId, 'nasr-city-rejected');
    await submitEditFlow(tester);

    expect(find.byType(OwnerPropertiesScreen), findsOneWidget);
    expect(find.text('قيد المراجعة'), findsOneWidget);
    expect(find.text('تمت إعادة إرسال العقار للمراجعة'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('connects add property from O-PROPS-01b', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerPropertiesScreen(initialProperties: ownerPropertiesFixture()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('إضافة عقار'));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerAddPropertyFlowScreen), findsOneWidget);
    expect(find.text('إضافة عقار جديد'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _OwnerPropertiesRepository implements BaseRepository {
  String? lastDetailsId;
  Map<String, dynamic>? lastUpdateBody;
  int updateRequestCount = 0;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
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
    final T data = params.mapper!(_propertyDetailsJson(propertyId));
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  Map<String, dynamic> _propertyDetailsJson(String propertyId) {
    return {
      'id': propertyId,
      'owner': 'owner-id',
      'main_image': 'https://example.com/main.jpg',
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
      'suitable_for': 'individuals',
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
      'latitude': '30.0444',
      'longitude': '31.2357',
      'amenities': ['wifi', 'garage'],
      'images': List<Map<String, dynamic>>.generate(
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
    };
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
      'owner_add_property_currency': 'ر.س',
      'owner_add_property_deposit': 'تأمين الشقة',
      'owner_add_property_rental_period': 'فترة التأجير',
      'owner_add_property_count': 'العدد',
      'owner_add_property_unit': 'الوحدة',
      'owner_add_property_rental_summary': 'فترة التأجير: {count} {unit}',
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
      'owner_add_property_monthly_price': '{price} ر.س/شهر',
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
