import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_add_property_flow_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
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
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
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
    final OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
        .copyWith(
          title: 'Cozy Studio',
          propertyType: 'استوديو',
          governorate: 'القاهرة',
          district: 'مدينة نصر',
          street: 'شارع النصر',
          bedrooms: '1',
          bathrooms: '1',
          space: '65',
          floor: '3',
          buildingYear: '2020',
          mapQuery: 'مدينة نصر، القاهرة',
          isLocationSelected: true,
          photos: photos,
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
    expect(body['main_image'], same(photos.first));
    expect(body['images'], hasLength(9));
    expect(body['ownership_proof'], same(ownershipProof));
    expect(body['has_wifi'], isTrue);
    expect(body['has_elevator'], isFalse);
  });

  testWidgets('runs O-PROPS-01b actions edit analytics and revenue', (
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

    await tester.tap(
      find.byKey(const ValueKey('owner-property-actions-nasr-city-furnished')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerPropertyActionSheet), findsOneWidget);
    expect(find.text('خيارات العقار'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('owner-property-action-pause')));
    await tester.pumpAndSettle();
    expect(find.text('تم إيقاف العقار مؤقتاً'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('owner-property-edit-nasr-city-furnished')),
    );
    await tester.pumpAndSettle();
    expect(find.byType(OwnerEditPropertyScreen), findsOneWidget);
    expect(find.text('تعديل العقار'), findsOneWidget);

    final Finder saveButton = find.byKey(const ValueKey('owner-edit-save'));
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
    await tester.pumpAndSettle();
    expect(find.byType(OwnerPropertiesScreen), findsOneWidget);
    expect(find.text('تم حفظ تعديلات العقار'), findsOneWidget);

    final Finder analyticsButton = find.byKey(
      const ValueKey('owner-property-analytics-nasr-city-furnished'),
    );
    await tester.ensureVisible(analyticsButton);
    await tester.tap(analyticsButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerPropertyAnalyticsScreen), findsOneWidget);
    expect(find.text('إحصاءات العقار'), findsOneWidget);
    expect(find.text('1,247'), findsOneWidget);

    final Finder revenueButton = find.byKey(
      const ValueKey('owner-analytics-revenue'),
    );
    await tester.drag(find.byType(ListView), const Offset(0, -700));
    await tester.pumpAndSettle();
    await tester.tap(revenueButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRevenueScreen), findsOneWidget);
    expect(find.text('الإيرادات'), findsOneWidget);
    expect(find.text('21,500 ج'), findsOneWidget);
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

    await tester.tap(
      find.byKey(const ValueKey('owner-property-card-nasr-city-rejected')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerPropertyRejectionScreen), findsOneWidget);
    expect(find.text('تم رفض عقارك'), findsOneWidget);
    expect(find.text('الصور غير واضحة أو لا تعبر عن العقار'), findsOneWidget);

    final Finder resubmitButton = find.byKey(
      const ValueKey('owner-property-rejection-edit-resubmit'),
    );
    await tester.scrollUntilVisible(resubmitButton, 260);
    await tester.drag(find.byType(ListView), const Offset(0, -140));
    await tester.pumpAndSettle();
    await tester.tap(resubmitButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerEditPropertyScreen), findsOneWidget);
    final Finder saveButton = find.byKey(const ValueKey('owner-edit-save'));
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
    await tester.pumpAndSettle();

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
    await tester.tap(find.byKey(const ValueKey('owner-properties-add')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerAddPropertyFlowScreen), findsOneWidget);
    expect(find.text('إضافة عقار جديد'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _OwnerPropertiesAssetLoader extends AssetLoader {
  const _OwnerPropertiesAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'home': 'الرئيسية',
      'chats': 'الشات',
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
