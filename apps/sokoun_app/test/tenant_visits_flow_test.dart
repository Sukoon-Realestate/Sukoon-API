import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_home_screen.dart';
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
            home: screen,
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

    await tester.pumpWidget(buildScreen(const TenantVisitsScreen()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(TenantVisitsContent.visits, hasLength(3));
    expect(find.byType(TenantVisitCard), findsNWidgets(3));
    expect(find.text('طلبات الزيارة'), findsOneWidget);
    expect(find.text('شقة مفروشة، مدينة نصر'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(
      find.byKey(const ValueKey('tenant-visit-accepted-nasr-city')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(VisitDetailsScreen), findsOneWidget);
    expect(find.text('زيارتك مؤكدة'), findsOneWidget);
    expect(find.text('010****432'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const ValueKey('visit-details-back')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('tenant-visit-rate-accepted-nasr-city')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(VisitRatingSheet), findsOneWidget);
    expect(find.text('قيّم تجربة الزيارة'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('visit-rating-overall-5')));
    await tester.enterText(
      find.byKey(const ValueKey('visit-rating-comment')),
      'تجربة ممتازة',
    );
    await tester.tap(find.byKey(const ValueKey('visit-rating-submit')));
    await tester.pumpAndSettle();

    expect(find.byType(VisitRatingSheet), findsNothing);
    expect(find.text('تم إرسال تقييمك بنجاح'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('filters and cancels a pending visit request', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantVisitsScreen()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    await tester.tap(
      find.byKey(const ValueKey('tenant-visits-filter-pending')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitCard), findsOneWidget);
    expect(find.text('ستوديو، التجمع الخامس'), findsOneWidget);

    await tester.tap(
      find.byKey(
        const ValueKey('tenant-visit-cancel-pending-fifth-settlement'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('لا توجد زيارات في هذه الفئة'), findsOneWidget);
    expect(find.text('تم إلغاء طلب الزيارة'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('runs booking and confirmation into my visits', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const BookVisitScreen()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('احجز زيارة'), findsOneWidget);
    expect(
      find.text('رقمك لن يُشارك مع المالك حتى تأكيد الزيارة'),
      findsOneWidget,
    );

    final Finder lastDay = find.byKey(const ValueKey('visit-day-18'));
    await tester.ensureVisible(lastDay);
    await tester.pumpAndSettle();
    await tester.tap(lastDay);
    await tester.tap(find.text('3:00 م'));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('visit-confirm-request')));
    await tester.pumpAndSettle();

    expect(find.byType(VisitConfirmedScreen), findsOneWidget);
    expect(find.text('تم إرسال طلب الزيارة!'), findsOneWidget);
    expect(find.text('الثلاثاء 18 يونيو'), findsOneWidget);
    expect(find.text('3:00 م'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const ValueKey('visit-follow-requests')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens my visits from the tenant home banner', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantHomeScreen()));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.byKey(const ValueKey('tenant-open-visits')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(find.text('شقة مفروشة، مدينة نصر'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
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
