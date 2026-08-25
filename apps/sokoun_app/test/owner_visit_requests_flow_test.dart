import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/visits/imports.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _OwnerTranslationsAssetLoader(),
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

  List<OwnerVisitRequestContent> ownerVisitRequestsFixture() {
    return const [
      OwnerVisitRequestContent(
        id: 'sara-nasr-city',
        initial: 'س',
        name: 'سارة أحمد خالد',
        property: 'شقة مفروشة — مدينة نصر',
        dateLabel: 'السبت 15 يونيو · 3:00 م',
        detailDate: 'السبت 15 يونيو 2025',
        time: '3:00 م',
        memberSince: 'مستأجر موثّق · عضو منذ 2024',
        tenantNote: 'مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب.',
        phone: '010****432',
        status: OwnerVisitRequestStatus.newRequest,
        isVerified: true,
      ),
      OwnerVisitRequestContent(
        id: 'mohamed-jeddah',
        initial: 'م',
        name: 'محمد أحمد',
        property: 'استوديو — جدة',
        dateLabel: 'الأحد 2:00 م',
        detailDate: 'الأحد 16 يونيو 2025',
        time: '2:00 م',
        memberSince: 'مستأجر موثّق · عضو منذ 2024',
        tenantNote: '',
        phone: '010****432',
        status: OwnerVisitRequestStatus.accepted,
        isVerified: true,
      ),
      OwnerVisitRequestContent(
        id: 'khaled-dammam',
        initial: 'خ',
        name: 'خالد عبدالله',
        property: 'غرفة — الدمام',
        dateLabel: 'الإثنين 11:00 ص',
        detailDate: 'الإثنين 17 يونيو 2025',
        time: '11:00 ص',
        memberSince: 'عضو منذ 2024',
        tenantNote: '',
        phone: '010****432',
        status: OwnerVisitRequestStatus.newRequest,
        isVerified: false,
      ),
    ];
  }

  test('maps received visit data from nested API fields', () {
    final List<OwnerVisitRequestContent> requests =
        OwnerVisitRequestContent.listFromResponse({
          'count': 1,
          'results': [
            {
              'id': 'visit-id',
              'property': {'id': 'property-id', 'title': 'Cozy Studio'},
              'tenant': {
                'full_name': 'Sara Ahmed',
                'phone': '01000000000',
                'is_verified': true,
              },
              'visit_date': '2026-09-15',
              'visit_time': '10:00:00',
              'note': 'Please confirm',
              'status': 'pending',
            },
          ],
        });

    expect(requests, hasLength(1));
    expect(requests.single.property, 'Cozy Studio');
    expect(requests.single.name, 'Sara Ahmed');
    expect(requests.single.tenantNote, 'Please confirm');
    expect(requests.single.status, OwnerVisitRequestStatus.pending);
  });

  testWidgets('opens O-REQ-02 and completes the O-ACCEPT flow', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('طلبات الزيارة'), findsOneWidget);
    expect(find.text('سارة أحمد خالد'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('owner-request-card-sara-nasr-city')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestDetailsScreen), findsOneWidget);
    expect(find.text('تفاصيل الطلب'), findsOneWidget);
    expect(find.text('ملاحظة المستأجر'), findsOneWidget);

    final Finder acceptButton = find.byKey(
      const ValueKey('owner-request-accept'),
    );
    await tester.ensureVisible(acceptButton);
    await tester.tap(acceptButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerAcceptRequestSheet), findsOneWidget);
    expect(find.text('قبول طلب الزيارة'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('owner-accept-confirm')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerVisitRequestsScreen), findsOneWidget);
    expect(find.text('تم قبول طلب الزيارة'), findsOneWidget);
    expect(find.text('تم القبول'), findsNWidgets(2));
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens O-REQ-02 and completes the O-REJECT flow', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('owner-request-card-sara-nasr-city')),
    );
    await tester.pumpAndSettle();

    final Finder rejectButton = find.byKey(
      const ValueKey('owner-request-reject'),
    );
    await tester.ensureVisible(rejectButton);
    await tester.tap(rejectButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRejectRequestSheet), findsOneWidget);
    expect(find.text('رفض طلب الزيارة'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('owner-reject-reason-propertyRented')),
    );
    await tester.tap(find.byKey(const ValueKey('owner-reject-confirm')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerVisitRequestsScreen), findsOneWidget);
    expect(find.text('تم رفض طلب الزيارة'), findsOneWidget);
    expect(find.text('تم الرفض'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens O-CAL-01 and edits O-AVAIL-01', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('owner-open-calendar')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestsCalendarScreen), findsOneWidget);
    expect(find.text('تقويم الزيارات'), findsOneWidget);
    expect(find.text('يناير 2025'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('owner-calendar-day-19')));
    await tester.pump();
    expect(find.text('زيارات يوم 19'), findsOneWidget);

    final Finder availabilityButton = find.byKey(
      const ValueKey('owner-open-availability'),
    );
    await tester.ensureVisible(availabilityButton);
    await tester.tap(availabilityButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerAvailabilityScreen), findsOneWidget);
    expect(find.text('مواعيد الاتاحة'), findsOneWidget);
    expect(find.text('الاثنين 15 يونيو'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('owner-availability-time-1')));
    await tester.tap(find.byKey(const ValueKey('owner-availability-save')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestsCalendarScreen), findsOneWidget);
    expect(find.text('تم حفظ مواعيد الإتاحة'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _OwnerTranslationsAssetLoader extends AssetLoader {
  const _OwnerTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'owner_visits_title': 'طلبات الزيارة',
      'owner_visits_total_requests': 'إجمالي الطلبات',
      'owner_visits_waiting_for_reply': 'بانتظار الرد',
      'owner_visits_filter_all': 'الكل',
      'owner_visits_filter_new': 'جديد',
      'owner_visits_filter_accepted': 'مقبول',
      'owner_visits_filter_rejected': 'مرفوض',
      'owner_visits_filter_completed': 'مكتمل',
      'owner_visits_no_requests': 'لا توجد طلبات في هذه الفئة',
      'owner_visit_status_new': 'جديد',
      'owner_visit_status_pending': 'انتظار',
      'owner_visit_status_accepted': 'تم القبول',
      'owner_visit_status_rejected': 'تم الرفض',
      'owner_visit_status_completed': 'مكتمل',
      'owner_visit_verified': 'موثّق',
      'owner_visit_accept': 'قبول',
      'owner_visit_reject': 'رفض',
      'owner_visit_accepted_message': 'تم قبول طلب الزيارة',
      'owner_visit_rejected_message': 'تم رفض طلب الزيارة',
      'owner_request_details_title': 'تفاصيل الطلب',
      'owner_visit_requested_property': 'العقار المطلوب',
      'owner_visit_request_date': 'تاريخ الزيارة',
      'owner_visit_request_time': 'الوقت',
      'owner_visit_tenant_note_title': 'ملاحظة المستأجر',
      'owner_visit_tenant_phone_hidden':
          'رقم المستأجر 010****432 — يظهر بعد القبول فقط',
      'owner_visit_accept_with_check': 'قبول الزيارة ✓',
      'owner_visit_reject_request': 'رفض الطلب',
      'owner_visit_open_chat': 'فتح المحادثة',
      'owner_accept_title': 'قبول طلب الزيارة',
      'owner_accept_subtitle': 'سيتم إشعار المستأجر فوراً',
      'owner_visit_tenant_label': 'المستأجر',
      'owner_accept_confirm': 'تأكيد القبول',
      'owner_request_cancel': 'إلغاء',
      'owner_reject_title': 'رفض طلب الزيارة',
      'owner_reject_subtitle': 'اختر سبب الرفض',
      'owner_reject_reason_inconvenient_time': 'الموعد غير مناسب',
      'owner_reject_reason_property_rented': 'العقار مؤجر حالياً',
      'owner_reject_reason_requirements_not_met': 'المستأجر لا يستوفي الشروط',
      'owner_reject_reason_other': 'سبب آخر',
      'owner_reject_confirm': 'تأكيد الرفض',
      'owner_visit_tenant_sara_initial': 'س',
      'owner_visit_tenant_sara': 'سارة أحمد خالد',
      'owner_visit_tenant_mohamed_initial': 'م',
      'owner_visit_tenant_mohamed': 'محمد أحمد',
      'owner_visit_tenant_khaled_initial': 'خ',
      'owner_visit_tenant_khaled': 'خالد عبدالله',
      'owner_visit_property_nasr_city': 'شقة مفروشة — مدينة نصر',
      'owner_visit_property_jeddah_studio': 'استوديو — جدة',
      'owner_visit_property_dammam_room': 'غرفة — الدمام',
      'owner_visit_date_saturday_at_three': 'السبت 15 يونيو · 3:00 م',
      'owner_visit_date_sunday_at_two': 'الأحد 2:00 م',
      'owner_visit_date_monday_at_eleven': 'الإثنين 11:00 ص',
      'owner_visit_date_saturday': 'السبت 15 يونيو 2025',
      'owner_visit_date_sunday': 'الأحد 16 يونيو 2025',
      'owner_visit_date_monday': 'الإثنين 17 يونيو 2025',
      'owner_visit_time_three_pm': '3:00 م',
      'owner_visit_time_two_pm': '2:00 م',
      'owner_visit_time_eleven_am': '11:00 ص',
      'owner_visit_verified_member_since': 'مستأجر موثّق · عضو منذ 2024',
      'owner_visit_member_since': 'عضو منذ 2024',
      'owner_visit_tenant_note':
          'مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب.',
      'owner_visit_tenant_phone': '010****432',
      'owner_calendar_title': 'تقويم الزيارات',
      'owner_calendar_month': 'يناير 2025',
      'owner_calendar_day_sunday_short': 'أح',
      'owner_calendar_day_monday_short': 'إث',
      'owner_calendar_day_tuesday_short': 'ثل',
      'owner_calendar_day_wednesday_short': 'أر',
      'owner_calendar_day_thursday_short': 'خم',
      'owner_calendar_day_friday_short': 'جم',
      'owner_calendar_day_saturday_short': 'سب',
      'owner_calendar_visits_on_day': 'زيارات يوم',
      'owner_calendar_tenant_sara_mahmoud': 'سارة محمود',
      'owner_calendar_time_five_thirty': '5:30 م',
      'owner_calendar_confirmed': 'مؤكدة',
      'owner_calendar_pending': 'معلقة',
      'owner_calendar_manage_availability': 'إدارة مواعيد الإتاحة',
      'owner_availability_title': 'مواعيد الاتاحة',
      'owner_availability_description':
          'اختر الأوقات المتاحة للزيارة هذا الأسبوع',
      'owner_availability_sunday': 'الأحد',
      'owner_availability_monday': 'الاثنين',
      'owner_availability_tuesday': 'الثلاثاء',
      'owner_availability_wednesday': 'الأربعاء',
      'owner_availability_thursday': 'الخميس',
      'owner_availability_friday': 'الجمعة',
      'owner_availability_saturday': 'السبت',
      'owner_availability_sunday_short': 'الأحد',
      'owner_availability_monday_short': 'الاثنين',
      'owner_availability_tuesday_short': 'الثلاثاء',
      'owner_availability_wednesday_short': 'الأربعاء',
      'owner_availability_thursday_short': 'الخميس',
      'owner_availability_friday_short': 'الجمعة',
      'owner_availability_saturday_short': 'السبت',
      'owner_availability_month_june': 'يونيو',
      'owner_availability_time_nine_am': '9:00 ص',
      'owner_availability_time_ten_am': '10:00 ص',
      'owner_availability_time_eleven_am': '11:00 ص',
      'owner_availability_time_noon': '12:00 م',
      'owner_availability_time_two_pm': '2:00 م',
      'owner_availability_time_three_pm': '3:00 م',
      'owner_availability_time_four_pm': '4:00 م',
      'owner_availability_time_five_pm': '5:00 م',
      'owner_availability_available': 'متاح',
      'owner_availability_booked': 'محجوز',
      'owner_availability_unspecified': 'غير محدد',
      'owner_availability_save': 'حفظ مواعيد الاتاحة',
      'owner_availability_saved': 'تم حفظ مواعيد الإتاحة',
    };
  }
}
