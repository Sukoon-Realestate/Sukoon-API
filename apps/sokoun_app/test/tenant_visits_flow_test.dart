import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import 'helpers/home_page_test_dependencies.dart';

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
    await CacheStorage.init();
    registerHomePageTestDependencies();
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
      assetLoader: const _CoreTranslationsAssetLoader(),
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
            home: Builder(
              builder: (context) => MediaQuery(
                data: MediaQuery.of(context).copyWith(disableAnimations: true),
                child: screen,
              ),
            ),
          );
        },
      ),
    );
  }

  void configurePhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  testWidgets('runs visits list detail and rating frames', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(TenantVisitsScreen(initialVisits: _tenantVisitFixtures())),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(_tenantVisitFixtures(), hasLength(3));
    expect(find.byType(TenantVisitCard), findsNWidgets(3));
    expect(find.text('طلبات الزيارة'), findsOneWidget);
    expect(find.text('شقة مفروشة، مدينة نصر'), findsOneWidget);
    expect(tester.takeException(), isNull);

    const Key acceptedVisitKey = ValueKey('accepted-nasr-city');
    await tester.tap(find.byKey(acceptedVisitKey));
    await tester.pumpAndSettle();

    expect(find.byType(VisitDetailsScreen), findsOneWidget);
    expect(find.text('زيارتك مؤكدة'), findsOneWidget);
    expect(find.text('010****432'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();
    await tester.tap(
      find.descendant(
        of: find.byKey(acceptedVisitKey),
        matching: find.text('تقييم'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(VisitRatingSheet), findsOneWidget);
    expect(find.text('قيّم تجربة الزيارة'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.star_border_rounded).at(4));
    await tester.enterText(find.byType(TextField), 'تجربة ممتازة');
    await tester.tap(find.text('إرسال التقييم'));
    await tester.pumpAndSettle();

    expect(find.byType(VisitRatingSheet), findsNothing);
    expect(find.text('تم إرسال تقييمك بنجاح'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('filters and cancels a pending visit request', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(TenantVisitsScreen(initialVisits: _tenantVisitFixtures())),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    await tester.tap(find.text('بانتظار'));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitCard), findsOneWidget);
    expect(find.text('ستوديو، التجمع الخامس'), findsOneWidget);

    await tester.tap(find.text('إلغاء الطلب'));
    await tester.pumpAndSettle();

    expect(find.text('لا توجد زيارات في هذه الفئة'), findsOneWidget);
    expect(find.text('تم إلغاء طلب الزيارة'), findsOneWidget);

    await tester.tap(find.text('عرض كل الزيارات'));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitCard), findsNWidgets(2));
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders the API empty state and opens property search', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantVisitsScreen()));
    await tester.pumpAndSettle();

    expect(find.text('لا توجد طلبات زيارة حتى الآن'), findsOneWidget);
    expect(find.text('تصفح العقارات'), findsOneWidget);

    await tester.tap(find.text('تصفح العقارات'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(TenantSearchScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders the pending T-VISIT-04 state', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(VisitDetailsScreen(visit: _tenantVisitFixtures()[1])),
    );
    await tester.pumpAndSettle();

    expect(find.text('زيارتك بانتظار التأكيد'), findsOneWidget);
    expect(find.text('إلغاء الطلب'), findsOneWidget);
    expect(find.text('فتح المحادثة مع المالك'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders unknown or rejected visits as a fail state', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(VisitDetailsScreen(visit: _tenantVisitFixtures()[2])),
    );
    await tester.pumpAndSettle();

    expect(find.text('تم رفض طلب الزيارة'), findsOneWidget);
    expect(find.text('البحث عن بديل'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('runs booking and confirmation into my visits', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const BookVisitScreen()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('احجز زيارة'), findsOneWidget);
    final DateTime today = DateUtils.dateOnly(DateTime.now());
    final BookVisitForm form = tester.widget<BookVisitForm>(
      find.byType(BookVisitForm),
    );
    expect(form.days, hasLength(7));
    expect(form.days.first.visitDate, _formatVisitDate(today));
    for (int index = 0; index < form.days.length; index++) {
      final DateTime expectedDate = DateTime(
        today.year,
        today.month,
        today.day + index,
      );
      expect(form.days[index].visitDate, _formatVisitDate(expectedDate));
    }
    expect(
      find.text('رقمك لن يُشارك مع المالك حتى تأكيد الزيارة'),
      findsOneWidget,
    );

    final Finder todayChip = find.text(today.day.toString());
    await tester.ensureVisible(todayChip);
    await tester.pumpAndSettle();
    await tester.tap(todayChip);
    await tester.tap(find.byType(VisitTimePickerField));
    await tester.pumpAndSettle();

    expect(find.byType(TimePickerDialog), findsOneWidget);
    final BuildContext pickerContext = tester.element(
      find.byType(TimePickerDialog),
    );
    final String okLabel = MaterialLocalizations.of(
      pickerContext,
    ).okButtonLabel;
    await tester.tap(find.widgetWithText(TextButton, okLabel).last);
    await tester.pumpAndSettle();

    expect(find.text('2:00 PM'), findsOneWidget);
    await tester.tap(find.text('تأكيد طلب الزيارة'));
    await tester.pumpAndSettle();

    expect(find.byType(VisitConfirmedScreen), findsOneWidget);
    expect(find.text('تم إرسال طلب الزيارة!'), findsOneWidget);
    final VisitConfirmedScreen confirmedScreen = tester.widget(
      find.byType(VisitConfirmedScreen),
    );
    expect(confirmedScreen.selectedDay.visitDate, _formatVisitDate(today));
    expect(find.text('2:00 PM'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('متابعة طلباتي'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens my visits from the tenant home banner', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantHomeScreen()));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('عندك زيارة النهارده 3:00 م'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

String _formatVisitDate(DateTime date) {
  final String month = date.month.toString().padLeft(2, '0');
  final String day = date.day.toString().padLeft(2, '0');
  return '${date.year}-$month-$day';
}

class _CoreTranslationsAssetLoader extends AssetLoader {
  const _CoreTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'home': 'الرئيسية',
      'favorites_navigation_saved': 'المحفوظات',
      'chats': 'الشات',
      'notifications': 'الإشعارات',
      'favorites_navigation_account': 'الحساب',
      'tenant_visits_title': 'طلبات الزيارة',
      'tenant_visits_filter_all': 'الكل',
      'tenant_visits_filter_accepted': 'مقبولة',
      'tenant_visits_filter_pending': 'بانتظار',
      'tenant_visits_filter_rejected': 'مرفوضة',
      'tenant_visits_no_results': 'لا توجد زيارات في هذه الفئة',
      'tenant_visits_empty_title': 'لا توجد طلبات زيارة حتى الآن',
      'tenant_visits_empty_description':
          'ستظهر هنا الزيارات التي تحجزها وآخر تحديث لحالتها.',
      'tenant_visits_filter_empty_description':
          'جرّب حالة أخرى أو اعرض كل طلبات الزيارة.',
      'tenant_visits_browse_properties': 'تصفح العقارات',
      'tenant_visits_show_all': 'عرض كل الزيارات',
      'tenant_home_suggested_for_you': 'مقترح لك',
      'tenant_home_view_all': 'عرض الكل',
      'tenant_home_greeting': 'أهلاً بك',
      'tenant_home_current_area': 'منطقتك الحالية',
      'tenant_home_search_area_hint': 'ابحث عن منطقة',
      'tenant_search_results_square_meters': 'م²',
      'favorites_currency_short': 'ج.م',
      'tenant_filter_monthly': 'شهرياً',
      'tenant_home_empty_title': 'لا توجد عقارات مقترحة',
      'tenant_home_empty_description': 'سنعرض لك عقارات مناسبة قريباً.',
      'tenant_visit_owner_label': 'المالك:',
      'tenant_visit_status_accepted': 'مقبول',
      'tenant_visit_status_accepted_with_check': 'مقبول ✓',
      'tenant_visit_status_pending': 'بانتظار الرد',
      'tenant_visit_status_rejected': 'مرفوض',
      'tenant_visit_chat_action': 'شات',
      'tenant_visit_rate_action': 'تقييم',
      'tenant_visit_cancel_request': 'إلغاء الطلب',
      'tenant_visit_find_alternative': 'البحث عن بديل',
      'tenant_visit_book_title': 'احجز زيارة',
      'tenant_visit_choose_day': 'اختار يوم الزيارة',
      'tenant_visit_choose_time': 'اختار الوقت',
      'tenant_visit_note_label': 'ملاحظة للمالك (اختياري)',
      'tenant_visit_note_hint': 'أي تفاصيل تريد ذكرها…',
      'tenant_visit_privacy_message':
          'رقمك لن يُشارك مع المالك حتى تأكيد الزيارة',
      'tenant_visit_confirm_request': 'تأكيد طلب الزيارة',
      'tenant_visit_confirmed_title': 'تم إرسال طلب الزيارة!',
      'tenant_visit_confirmed_description':
          'المالك سيرد عليك خلال 24 ساعة. هتلاقي تحديثات في الإشعارات.',
      'tenant_visit_summary_property': 'العقار',
      'tenant_visit_summary_day': 'اليوم',
      'tenant_visit_summary_time': 'الوقت',
      'tenant_visit_summary_status': 'الحالة',
      'tenant_visit_pending_owner_response': 'بانتظار رد المالك',
      'tenant_visit_follow_requests': 'متابعة طلباتي',
      'tenant_visit_back_to_search': 'ارجع للبحث',
      'tenant_visit_details_title': 'تفاصيل الزيارة',
      'tenant_visit_confirmed_heading': 'زيارتك مؤكدة',
      'tenant_visit_pending_heading': 'زيارتك بانتظار التأكيد',
      'tenant_visit_rejected_heading': 'تم رفض طلب الزيارة',
      'tenant_visit_contact_info': 'معلومات التواصل',
      'tenant_visit_owner_phone_confirmed': 'رقم المالك — بعد التأكيد',
      'tenant_visit_open_owner_chat': 'فتح المحادثة مع المالك',
      'tenant_visit_cancel_visit': 'إلغاء الزيارة',
      'tenant_visit_rate_title': 'قيّم تجربة الزيارة',
      'tenant_visit_rating_cleanliness': 'النظافة',
      'tenant_visit_rating_accuracy': 'الدقة في البيانات',
      'tenant_visit_rating_owner_treatment': 'تعامل المالك',
      'tenant_visit_rating_comment_hint': 'اكتب تعليقك… (اختياري)',
      'tenant_visit_rating_submit': 'إرسال التقييم',
      'tenant_visit_rating_submitted': 'تم إرسال تقييمك بنجاح',
      'tenant_visit_request_canceled': 'تم إلغاء طلب الزيارة',
      'tenant_visit_property_nasr_city': 'شقة مفروشة، مدينة نصر',
      'tenant_visit_owner_ahmed': 'أحمد محمد',
      'tenant_visit_date_today': 'النهارده 3:00 م',
      'tenant_visit_property_fifth_settlement': 'ستوديو، التجمع الخامس',
      'tenant_visit_owner_mona': 'منى علي',
      'tenant_visit_date_tomorrow': 'غداً 12:00 م',
      'tenant_visit_property_mohandessin': 'شقة، المهندسين',
      'tenant_visit_owner_khaled': 'خالد حسن',
      'tenant_visit_date_thursday': 'الخميس 5:00 م',
      'tenant_visit_banner_title': 'عندك زيارة النهارده 3:00 م',
      'tenant_visit_banner_property': 'شقة مدينة نصر',
      'tenant_visit_booking_property_title': 'شقة مفروشة — مدينة نصر',
      'tenant_visit_booking_property_meta': '6,500 ج/شهر · 3 غرف',
      'tenant_visit_detail_date': 'السبت 15 يونيو 2025',
      'tenant_visit_detail_phone': '010****432',
      'tenant_visit_day_friday': 'الجمعة',
      'tenant_visit_day_saturday': 'السبت',
      'tenant_visit_day_sunday': 'الأحد',
      'tenant_visit_day_monday': 'الاثنين',
      'tenant_visit_day_tuesday': 'الثلاثاء',
      'tenant_visit_day_wednesday': 'الأربعاء',
      'tenant_visit_day_thursday': 'الخميس',
      'tenant_visit_month_june': 'يونيو',
      'tenant_visit_time_ten_am': '10:00 ص',
      'tenant_visit_time_eleven_am': '11:00 ص',
      'tenant_visit_time_noon': '12:00 م',
      'tenant_visit_time_two_pm': '2:00 م',
      'tenant_visit_time_three_pm': '3:00 م',
      'tenant_visit_time_five_pm': '5:00 م',
    };
  }
}

List<TenantVisitContent> _tenantVisitFixtures() {
  return const [
    TenantVisitContent(
      id: 'accepted-nasr-city',
      propertyTitle: 'شقة مفروشة، مدينة نصر',
      day: 'السبت 15 يونيو 2025',
      time: '2:00 م',
      status: TenantVisitStatus.accepted,
      statusText: 'مقبول',
      ownerName: 'أحمد محمد',
      ownerPhone: '010****432',
    ),
    TenantVisitContent(
      id: 'pending-fifth-settlement',
      propertyTitle: 'ستوديو، التجمع الخامس',
      day: 'غداً',
      time: '12:00 م',
      status: TenantVisitStatus.pending,
      statusText: 'بانتظار الرد',
      ownerName: 'منى علي',
    ),
    TenantVisitContent(
      id: 'rejected-mohandessin',
      propertyTitle: 'شقة، المهندسين',
      day: 'الخميس',
      time: '5:00 م',
      status: TenantVisitStatus.rejected,
      statusText: 'مرفوض',
      ownerName: 'خالد حسن',
    ),
  ];
}
