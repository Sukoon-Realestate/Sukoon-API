import 'package:sokoun_app/features/tenant/visits/data/visit_schedule_rules.dart';
import 'package:toastification/toastification.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'dart:async';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import 'helpers/home_page_test_dependencies.dart';
import 'helpers/account_test_dependencies.dart';

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
    await injector.unregister<BaseCrudUseCase>();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: _VisitsRepository()),
    );
    await registerAuthenticatedTestAccount();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
  });

  setUp(() {
    toastification.managers.clear();
    _slotTaken = false;
    _bookingPosts = 0;
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
            navigatorObservers: [AppNavigationObserver.instance],
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
    expect(find.text('+201001234567'), findsOneWidget);
    expect(find.text('010****432'), findsNothing);
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

    for (int i = 0; i < 3; i++) {
      final stars = find
          .descendant(
            of: find.byType(VisitRatingStars).at(i),
            matching: find.byIcon(Icons.star_border_rounded),
          )
          .last;
      await tester.ensureVisible(stars);
      await tester.tap(stars);
      await tester.pump();
    }
    await tester.enterText(find.byType(TextField), 'تجربة ممتازة');
    await tester.tap(find.text('إرسال التقييم'));
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byType(VisitRatingSheet), findsNothing);
    expect(find.text('Server accepted the visit rating'), findsOneWidget);
    toastification.dismissAll(delayForAnimation: false);
    await tester.pump(const Duration(seconds: 1));
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

    expect(find.byType(AlertDialog), findsOneWidget);
    expect(find.text('ستوديو، التجمع الخامس'), findsNWidgets(2));
    await tester.tap(find.text(LocaleKeys.visitKeepBooking));
    await tester.pumpAndSettle();
    expect(find.byType(TenantVisitCard), findsOneWidget);
    await tester.tap(find.text('إلغاء الطلب'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(LocaleKeys.visitConfirmCancellation));
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('لا توجد زيارات في هذه الفئة'), findsOneWidget);
    expect(find.text('Server canceled the visit request'), findsOneWidget);
    toastification.dismissAll(delayForAnimation: false);
    await tester.pump(const Duration(seconds: 1));

    await tester.tap(find.text('عرض كل الزيارات'));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitCard), findsNWidgets(3));
    final cards = tester.widgetList<TenantVisitCard>(
      find.byType(TenantVisitCard),
    );
    final canceled = cards.singleWhere(
      (card) => card.visit.propertyTitle == 'ستوديو، التجمع الخامس',
    );
    expect(canceled.visit.status, TenantVisitStatus.canceled);
    expect(canceled.visit.canCancel, isFalse);
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
    final EditableText searchInput = tester.widget<EditableText>(
      find.byType(EditableText).first,
    );
    expect(searchInput.controller.text, isEmpty);
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

  testWidgets(
    'a slot taken during selection clears the choice and submits nothing',
    (tester) async {
      configurePhoneViewport(tester);
      await tester.pumpWidget(
        buildScreen(
          const BookVisitScreen(
            property: VisitPropertyContent(
              id: 'property-conflict',
              ownerId: 'other-owner',
              title: 'Test property',
              meta: '',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final label = const TimeOfDay(
        hour: 14,
        minute: 0,
      ).format(tester.element(find.byType(VisitAvailableTimes)));
      await tester.tap(find.widgetWithText(ChoiceChip, label));
      await tester.pump();
      _slotTaken = true;
      await tester.tap(find.text('تأكيد طلب الزيارة'));
      await tester.pumpAndSettle();
      expect(find.byType(VisitRequestReviewSheet), findsNothing);
      expect(find.byType(VisitConfirmedScreen), findsNothing);
      expect(
        tester.widget<BookVisitForm>(find.byType(BookVisitForm)).selectedTime,
        isNull,
      );
      expect(_bookingPosts, 0);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('runs booking and confirmation into my visits', (tester) async {
    configurePhoneViewport(tester);

    WorkspaceTab? selectedTab;
    Future<void> selectWorkspace(
      AppWorkspace? workspace,
      WorkspaceTab? tab,
    ) async {
      expect(workspace, AppWorkspace.tenant);
      selectedTab = tab;
    }

    WorkspaceNavigation.attach(selectWorkspace);
    addTearDown(() => WorkspaceNavigation.detach(selectWorkspace));
    await tester.pumpWidget(
      buildScreen(TenantVisitsScreen(initialVisits: _tenantVisitFixtures())),
    );
    await tester.pumpAndSettle();
    unawaited(
      Go.to(
        const BookVisitScreen(
          property: VisitPropertyContent(
            id: 'booking-property',
            ownerId: 'booking-owner',
            title: 'Test property',
            meta: 'Test price',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('احجز زيارة'), findsOneWidget);
    final today = _bookingDate();
    final form = tester.widget<BookVisitForm>(find.byType(BookVisitForm));
    expect(form.days, hasLength(3));
    expect(form.days.first.visitDate, _formatVisitDate(today));
    expect(find.byType(VisitTimePickerField), findsNothing);
    expect(find.byType(TimePickerDialog), findsNothing);
    final timeLabel = const TimeOfDay(
      hour: 14,
      minute: 0,
    ).format(tester.element(find.byType(VisitAvailableTimes)));
    await tester.ensureVisible(find.widgetWithText(ChoiceChip, timeLabel));
    await tester.tap(find.widgetWithText(ChoiceChip, timeLabel));
    await tester.pump();
    await tester.tap(find.text('تأكيد طلب الزيارة'));
    // The original button stays busy while the review sheet is awaiting a choice.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();

    expect(find.byType(VisitConfirmedScreen), findsNothing);
    await tester.tap(find.text(LocaleKeys.tenantVisitConfirmRequest).last);
    await tester.pumpAndSettle();

    expect(find.byType(VisitConfirmedScreen), findsOneWidget);
    expect(find.text(LocaleKeys.freeVisitRequestSent), findsOneWidget);
    final VisitConfirmedScreen confirmedScreen = tester.widget(
      find.byType(VisitConfirmedScreen),
    );
    expect(confirmedScreen.selectedDay.visitDate, _formatVisitDate(today));
    expect(find.text(timeLabel), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('متابعة طلباتي'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(selectedTab, WorkspaceTab.visits);
    expect(find.byType(VisitConfirmedScreen), findsNothing);
    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens my visits from the tenant home banner', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantHomeScreen()));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('visit'), findsOneWidget);
    expect(find.text('عندك زيارة النهارده 3:00 م'), findsNothing);
    await tester.tap(find.text('visit'));
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
      'egyptian_pound_short': 'ج.م',
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
      visitDate: '2025-06-15',
      visitTime: '14:00:00',
      propertyTitle: 'شقة مفروشة، مدينة نصر',
      day: 'السبت 15 يونيو 2025',
      time: '2:00 م',
      status: TenantVisitStatus.accepted,
      statusText: 'مقبول',
      ownerName: 'أحمد محمد',
      ownerPhone: '+201001234567',
      isPhoneRevealed: true,
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

DateTime _bookingDate() {
  final current = VisitScheduleRules.now();
  return DateTime(current.year, current.month, current.day + 1);
}

bool _slotTaken = false;
int _bookingPosts = 0;

class _VisitsRepository implements BaseRepository {
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.httpRequestType == HttpRequestType.post &&
        params.api.contains('properties/')) {
      _bookingPosts++;
    }
    final String id = params.api.split('/').where((s) => s.isNotEmpty).last;
    final visit = _tenantVisitFixtures().where((v) => v.id == id).firstOrNull;
    final Map<String, dynamic> json = params.api.endsWith('/available_dates/')
        ? (params.queryParameters?['date'] == null
              ? <String, dynamic>{
                  'days': [
                    for (var index = 0; index < 3; index++)
                      {
                        'day':
                            [
                              'monday',
                              'tuesday',
                              'wednesday',
                              'thursday',
                              'friday',
                              'saturday',
                              'sunday',
                            ][_bookingDate()
                                    .add(Duration(days: index))
                                    .weekday -
                                1],
                        'date':
                            '${_bookingDate().add(Duration(days: index)).day}/${_bookingDate().month}',
                        'visit_date': _formatVisitDate(
                          _bookingDate().add(Duration(days: index)),
                        ),
                      },
                  ],
                }
              : <String, dynamic>{
                  'times': [
                    {
                      'time': '2:00 PM',
                      'visit_time': '14:00:00',
                      'is_available': !_slotTaken,
                    },
                    {
                      'time': '4:00 PM',
                      'visit_time': '16:00:00',
                      'is_available': false,
                    },
                  ],
                })
        : visit?.toJson() ??
              const <String, dynamic>{
                'count': 0,
                'results': [],
                'banner': 'visit',
              };
    final String message = params.api.endsWith('/review/')
        ? 'Server accepted the visit rating'
        : params.httpRequestType == HttpRequestType.patch
        ? 'Server canceled the visit request'
        : params.httpRequestType == HttpRequestType.post
        ? 'Server received the visit request'
        : '';
    return Success(
      BaseModel<T>(key: '', msg: message, data: params.mapper!(json)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
