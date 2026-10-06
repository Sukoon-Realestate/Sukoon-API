import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_visit_requests/imports.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_request_card.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_requests_response.dart';
import 'package:sokoun_app/features/owner/visits/data/owner_visit_requests_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_page_response.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_read_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

late final Map<String, dynamic> _ownerEnglishTranslations;

Map<String, dynamic> _ownerRequestDetailsResponse(String id) {
  final bool canChat = id == 'chat-enabled';
  return {
    'id': id,
    'tenant': {
      'id': 'tenant-id',
      'name': 'سارة أحمد خالد',
      'avatar': '',
      'is_verified': true,
      'member_since_year': 2024,
      'membership_label': 'مستأجر موثّق · عضو منذ 2024',
      'phone_number': '',
      'masked_phone_number': '010****432',
      'is_phone_revealed': false,
      'phone_notice': 'رقم المستأجر 010****432 – يظهر بعد القبول فقط',
    },
    'property': {
      'id': 'owner-property-id',
      'title': 'شقة مفروشة',
      'district': 'مدينة نصر',
      'display_name': 'شقة مفروشة – مدينة نصر',
    },
    'visit_date': '2025-06-15',
    'visit_time': '15:00:00',
    'day_label': 'السبت 15 يونيو 2025',
    'time_label': '3:00 م',
    'note': 'مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب.',
    'status': canChat ? 'accepted' : 'pending',
    'status_label': canChat ? 'تم القبول' : 'بانتظار رد المالك',
    'actions': {
      'can_accept': !canChat,
      'can_reject': !canChat,
      'can_chat': canChat,
    },
    'created_at': '2026-09-05T18:00:00Z',
  };
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  late _RecordingBaseRepository repository;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    _ownerEnglishTranslations = Map<String, dynamic>.from(
      jsonDecode(
            await rootBundle.loadString(
              'packages/melos_core/assets/translations/en.json',
            ),
          )
          as Map,
    );
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold']) {
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
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity'),
          (_) async => ['wifi'],
        );
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  setUp(() async {
    await injector.reset();
    repository = _RecordingBaseRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    injector.registerSingleton<ChatDataSource>(const _OwnerChatDataSource());
  });

  tearDown(() => injector.reset());

  Widget buildScreen(
    Widget screen, {
    String language = 'ar',
    double textScale = 1,
  }) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      path: 'unused',
      assetLoader: const _OwnerTranslationsAssetLoader(),
      startLocale: Locale(language),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        enableScaleWH: () => false,
        enableScaleText: () => false,
        builder: (context, _) {
          return MaterialApp(
            theme: SokounTheme.light,
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: TextScaler.linear(textScale)),
              child: child!,
            ),
            home: RepaintBoundary(child: screen),
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
        propertyId: 'owner-property-id',
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
    expect(
      OwnerVisitRequestStatusExtension.fromName('confirmed'),
      OwnerVisitRequestStatus.accepted,
    );
    expect(
      OwnerVisitRequestStatusExtension.fromName('canceled'),
      OwnerVisitRequestStatus.canceled,
    );
  });

  Map<String, dynamic> requestsPage({
    required List<OwnerVisitRequestContent> requests,
    int count = 40,
    int? nextPage,
    Map<String, int> tabs = const {'all': 40, 'new': 20, 'confirmed': 20},
  }) => {
    'count': count,
    'next': nextPage == null
        ? null
        : 'https://example.com/requests/?page=$nextPage',
    'tabs': tabs,
    'results': requests.map((request) => request.toJson()).toList(),
  };

  List<OwnerVisitRequestContent> pageRequests(int start, int length) =>
      List.generate(
        length,
        (index) => ownerVisitRequestsFixture().first.copyWith(
          id: 'page-request-${start + index}',
          name: 'سارة ${start + index}',
        ),
      );

  test(
    'owner request pages follow server links and serialize cached metadata',
    () async {
      repository.visitPages[1] = requestsPage(
        requests: pageRequests(0, 20),
        nextPage: 3,
      );
      repository.visitPages[3] = requestsPage(requests: pageRequests(20, 20));
      final data = OwnerVisitRequestsData(requests: true);
      final first = await data.getPage(
        page: 1,
        filter: OwnerVisitRequestFilter.all,
      );
      final second = await data.getPage(
        page: 2,
        filter: OwnerVisitRequestFilter.all,
      );
      expect(
        repository.requests.map((request) => request.queryParameters?['page']),
        [1, 3],
      );
      expect(first.$2.totalPages, 2);
      expect(second.$2.totalPages, 2);
      expect(second.$1.results.first.id, 'page-request-20');
      expect(
        repository.requests.first.cacheKey,
        isNot(repository.requests.last.cacheKey),
      );
      expect(OwnerVisitRequestsResponse.fromJson(first.$1.toJson()), first.$1);
      final params =
          repository.requests.first
              as CrudBaseParmas<OwnerVisitRequestsResponse>;
      expect(params.fromCacheJson!(params.toJson!(first.$1)), first.$1);
      final refresh = await data.getPage(
        page: 1,
        filter: OwnerVisitRequestFilter.all,
      );
      expect(repository.requests.last.queryParameters, {'page': 1});
      expect(refresh.$1.results.first.id, 'page-request-0');
    },
  );

  test(
    'filters continue through empty earlier pages and keep server tab counts',
    () async {
      repository.visitPages[1] = requestsPage(
        requests: pageRequests(0, 2),
        nextPage: 2,
      );
      repository.visitPages[2] = requestsPage(
        requests: [ownerVisitRequestsFixture()[1]],
        tabs: const {},
      );
      final data = OwnerVisitRequestsData(requests: false);
      final filtered = await data.getPage(
        page: 1,
        filter: OwnerVisitRequestFilter.accepted,
      );
      expect(
        repository.requests.map((request) => request.queryParameters?['page']),
        [1, 2],
      );
      expect(repository.lastApi, 'properties/visits/received/');
      expect(
        filtered.$1.results.single.status,
        OwnerVisitRequestStatus.accepted,
      );
      expect(filtered.$1.tabs['all'], 40);
      expect(filtered.$2.totalPages, 1);
    },
  );

  testWidgets(
    'summary, filters and cards scroll together and load the next page',
    (tester) async {
      configurePhoneViewport(tester);
      repository.visitPages[1] = requestsPage(
        requests: pageRequests(0, 20),
        nextPage: 2,
      );
      repository.visitPages[2] = requestsPage(requests: pageRequests(20, 20));
      await tester.pumpWidget(buildScreen(const OwnerVisitRequestsScreen()));
      await tester.pumpAndSettle();
      final pagify = tester.widget<AppPagify<OwnerVisitRequestContent>>(
        find.byType(AppPagify<OwnerVisitRequestContent>),
      );
      expect(pagify.pagifyController.items, hasLength(20));
      expect(
        find.descendant(
          of: find.byType(OwnerVisitRequestSummaryGrid),
          matching: find.text('40'),
        ),
        findsOneWidget,
      );
      final sections = [
        find.byType(OwnerVisitRequestSummaryGrid),
        find.byType(OwnerVisitRequestFilters),
        find.byType(OwnerVisitRequestCard).first,
      ];
      final tops = [
        for (final section in sections) tester.getTopLeft(section).dy,
      ];
      final scrollable = tester.state<ScrollableState>(
        find
            .descendant(
              of: find.byType(AppPagify<OwnerVisitRequestContent>),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await tester.drag(
        find.byType(OwnerVisitRequestSummaryGrid),
        const Offset(0, -120),
      );
      await tester.pumpAndSettle();
      expect(scrollable.position.pixels, greaterThan(0));
      for (int index = 0; index < sections.length; index++) {
        expect(
          tops[index] - tester.getTopLeft(sections[index]).dy,
          closeTo(scrollable.position.pixels, 0.1),
        );
      }
      scrollable.position.jumpTo(scrollable.position.maxScrollExtent);
      await tester.pumpAndSettle();
      expect(pagify.pagifyController.items, hasLength(40));
      expect(
        repository.requests.map((request) => request.queryParameters?['page']),
        [1, 2],
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('empty and error states retain the header and refresh from it', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    repository.visitsUnavailable = true;
    await tester.pumpWidget(buildScreen(const OwnerVisitRequestsScreen()));
    await tester.pumpAndSettle();
    expect(find.byType(OwnerVisitRequestsHeader), findsOneWidget);
    expect(find.byType(ExceptionView), findsOneWidget);
    repository.visitsUnavailable = false;
    final retry = tester.widget<ExceptionView>(find.byType(ExceptionView));
    await retry.onRetry!();
    await tester.pumpAndSettle();
    expect(find.byType(OwnerVisitRequestsEmptyState), findsOneWidget);
    expect(find.byType(OwnerVisitRequestsHeader), findsOneWidget);
    final int requestsBeforeRefresh = repository.requests.length;
    repository.visitPages[1] = requestsPage(
      requests: pageRequests(0, 1),
      count: 1,
    );
    await tester.drag(
      find.byType(OwnerVisitRequestSummaryGrid),
      const Offset(0, 350),
    );
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(repository.requests.length, requestsBeforeRefresh + 1);
    expect(find.byType(OwnerVisitRequestCard), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      for (final language in ['ar', 'en']) {
        testWidgets('paginated requests $language width=$width text=$scale', (
          tester,
        ) async {
          tester.view.physicalSize = Size(width, width >= 1024 ? 768 : 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          repository.visitPages[1] = requestsPage(
            requests: pageRequests(0, 20),
          );
          await tester.pumpWidget(
            buildScreen(
              const OwnerVisitRequestsScreen(),
              language: language,
              textScale: scale,
            ),
          );
          await tester.pumpAndSettle();
          expect(find.byType(OwnerVisitRequestsHeader), findsOneWidget);
          expect(tester.takeException(), isNull);
          if (scale == 1 && (width == 390 || width == 1024)) {
            final boundary = tester.renderObject<RenderRepaintBoundary>(
              find
                  .ancestor(
                    of: find.byType(OwnerVisitRequestsScreen),
                    matching: find.byType(RepaintBoundary),
                  )
                  .first,
            );
            await tester.runAsync(() async {
              final image = await boundary.toImage(pixelRatio: 1);
              final bytes = await image.toByteData(
                format: ui.ImageByteFormat.png,
              );
              final output = Directory('../../build/full_screen_pagination')
                ..createSync(recursive: true);
              await File(
                '${output.path}/owner-requests-$language-${width.toInt()}.png',
              ).writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
        });
      }
    }
  }

  test('maps and serializes owner visit request details', () {
    final OwnerVisitRequestDetailsContent request =
        OwnerVisitRequestDetailsContent.fromJson(
          _ownerRequestDetailsResponse('visit-id'),
        );

    expect(request.id, 'visit-id');
    expect(request.tenant.name, 'سارة أحمد خالد');
    expect(request.tenant.memberSinceYear, 2024);
    expect(request.tenant.displayPhone, '010****432');
    expect(request.property.displayName, 'شقة مفروشة – مدينة نصر');
    expect(request.displayDate, 'السبت 15 يونيو 2025');
    expect(request.displayTime, '3:00 م');
    expect(request.displayStatus, 'بانتظار رد المالك');
    expect(request.actions.canAccept, isTrue);
    expect(request.actions.canChat, isFalse);
    expect(OwnerVisitRequestDetailsContent.fromJson(request.toJson()), request);
  });

  test('loads owner visit request details from the owner endpoint', () async {
    final OwnerRequestDetailsCubit cubit = OwnerRequestDetailsCubit();
    addTearDown(cubit.close);

    await cubit.getRequestDetails('visit-id');

    expect(repository.lastApi, 'properties/owner/visits/requests/visit-id/');
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, 'owner_visit_request_details_visit-id');
    expect(cubit.data.tenant.name, 'سارة أحمد خالد');
  });

  test('accepts and rejects through the owner request actions', () async {
    final OwnerVisitStatusCubit cubit = OwnerVisitStatusCubit();
    addTearDown(cubit.close);

    bool accepted = false;
    await cubit.acceptVisitRequest(
      requestId: 'visit-id',
      onSuccess: () => accepted = true,
    );

    expect(
      repository.lastApi,
      'properties/owner/visits/requests/visit-id/accept/',
    );
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, isNull);
    expect(accepted, isTrue);

    bool rejected = false;
    await cubit.rejectVisitRequest(
      requestId: 'visit-id',
      onSuccess: () => rejected = true,
    );

    expect(
      repository.lastApi,
      'properties/owner/visits/requests/visit-id/reject/',
    );
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, {
      'reason': 'timing_not_suitable',
      'custom_reason': '',
    });
    expect(rejected, isTrue);
  });

  test('loads the owner calendar with year, month, and date queries', () async {
    final OwnerCalendarCubit cubit = OwnerCalendarCubit(
      initialDate: DateTime(2026, 9, 7),
    );
    addTearDown(cubit.close);

    await cubit.getCalendar(date: DateTime(2026, 9, 7));

    expect(repository.lastApi, 'properties/owner/calendar/');
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastQuery, {
      'year': 2026,
      'month': 9,
      'date': '2026-09-07',
    });
  });

  test('maps the nested owner calendar response', () {
    final OwnerVisitCalendarContent calendar =
        OwnerVisitCalendarContent.fromJson({
          'year': 2026,
          'month': 9,
          'days': [
            {'date': '2026-09-07', 'day': 7, 'visit_count': 1},
          ],
          'selected_date': '2026-09-07',
          'visits': [
            {
              'id': 'visit-id',
              'tenant': {'id': 'tenant-id', 'name': 'Mahmoud Salama'},
              'property': {
                'id': 'property-id',
                'title': 'Cozy Studio Near Metro Station',
              },
              'visit_time': '09:00:00',
              'status': 'pending',
            },
          ],
        });

    expect(calendar.days.single.visitCount, 1);
    expect(calendar.visits.single.tenant.name, 'Mahmoud Salama');
    expect(calendar.visits.single.property.id, 'property-id');
    expect(calendar.visits.single.visitTime, '09:00:00');
    expect(calendar.firstPropertyId, 'property-id');
    expect(OwnerVisitCalendarContent.fromJson(calendar.toJson()), calendar);
  });

  test('saves and maps owner property availability', () async {
    final OwnerAvailabilityCubit cubit = OwnerAvailabilityCubit();
    addTearDown(cubit.close);
    const OwnerAvailabilitySaveBody body = OwnerAvailabilitySaveBody(
      availabilityDate: '2026-09-07',
      slots: [
        OwnerAvailabilitySlotBody(time: '09:00:00', isEnabled: true),
        OwnerAvailabilitySlotBody(time: '12:00:00', isEnabled: true),
        OwnerAvailabilitySlotBody(time: '16:00:00', isEnabled: false),
      ],
    );

    final bool saved = await cubit.saveAvailability(
      ownerPropertyId: 'property-id',
      body: body,
    );

    expect(saved, isTrue);
    expect(
      repository.lastApi,
      'properties/owner/properties/property-id/availability/',
    );
    expect(repository.lastMethod, HttpRequestType.put);
    expect(repository.lastBody, body.toJson());

    final OwnerAvailabilityScheduleContent schedule =
        OwnerAvailabilityScheduleContent.fromJson({
          'week_start': '2026-09-07',
          'week_end': '2026-09-13',
          'days': [
            {
              'date': '2026-09-07',
              'day': 'monday',
              'slots': [
                {
                  'id': 'slot-id',
                  'time': '09:00:00',
                  'is_enabled': true,
                  'state': 'available',
                  'visit': null,
                },
              ],
            },
          ],
        });

    expect(schedule.weekEnd, '2026-09-13');
    expect(schedule.days.single.dayName, 'monday');
    expect(
      schedule.days.single.slots.single.slotState,
      OwnerAvailabilitySlotState.available,
    );
    expect(
      OwnerAvailabilityScheduleContent.fromJson(schedule.toJson()),
      schedule,
    );
  });

  testWidgets('renders the O-REQ-ICON-B request card states', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('sara-nasr-city')), findsOneWidget);
    expect(find.byKey(const ValueKey('mohamed-jeddah')), findsOneWidget);
    expect(find.byIcon(Icons.chat_bubble_outline_rounded), findsNWidgets(3));
    expect(find.text('السبت 15 يونيو · 3:00 م'), findsOneWidget);
    expect(find.text('تم القبول'), findsOneWidget);
    expect(find.text('قبول'), findsNWidgets(2));
    expect(find.text('رفض'), findsNWidgets(2));
    expect(tester.takeException(), isNull);
  });

  testWidgets('list accept action uses the owner request API', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();

    final Finder requestCard = find.byKey(const ValueKey('sara-nasr-city'));
    await tester.tap(
      find.descendant(of: requestCard, matching: find.text('قبول')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('تأكيد القبول'));
    await tester.pumpAndSettle();

    expect(
      repository.lastApi,
      'properties/owner/visits/requests/sara-nasr-city/accept/',
    );
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, isNull);
    expect(
      find.descendant(of: requestCard, matching: find.text('تم القبول')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('dashboard request card opens API-backed request details', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        const Scaffold(
          body: OwnerRequestCard(
            requestId: 'dashboard-visit-id',
            name: 'سارة أحمد خالد',
            details: 'شقة مفروشة · مدينة نصر · 3:00 م',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(OwnerRequestCard));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestDetailsScreen), findsOneWidget);
    expect(
      repository.lastApi,
      'properties/owner/visits/requests/dashboard-visit-id/',
    );
    expect(repository.lastMethod, HttpRequestType.get);
    expect(find.text('شقة مفروشة – مدينة نصر'), findsOneWidget);
    expect(find.text('بانتظار رد المالك'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens chat when the request API allows chat', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(const OwnerRequestDetailsScreen(requestId: 'chat-enabled')),
    );
    await tester.pumpAndSettle();

    final Finder chatButton = find.text('فتح المحادثة');
    await tester.ensureVisible(chatButton);
    await tester.tap(chatButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pump(const Duration(milliseconds: 700));

    expect(find.byType(ChatScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
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

    await tester.tap(find.byKey(const ValueKey('sara-nasr-city')));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestDetailsScreen), findsOneWidget);
    expect(find.text('تفاصيل الطلب'), findsOneWidget);
    expect(find.text('ملاحظة المستأجر'), findsOneWidget);

    final Finder acceptButton = find.text('قبول الزيارة ✓');
    await tester.ensureVisible(acceptButton);
    await tester.tap(acceptButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerAcceptRequestSheet), findsOneWidget);
    expect(find.text('قبول طلب الزيارة'), findsOneWidget);

    await tester.tap(find.text('تأكيد القبول'));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerVisitRequestsScreen), findsOneWidget);
    expect(find.byType(OwnerAcceptRequestSheet), findsNothing);
    expect(find.text('تم القبول'), findsNWidgets(2));
    expect(
      repository.lastApi,
      'properties/owner/visits/requests/sara-nasr-city/accept/',
    );
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, isNull);
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
    await tester.tap(find.byKey(const ValueKey('sara-nasr-city')));
    await tester.pumpAndSettle();

    final Finder rejectButton = find.text('رفض الطلب');
    await tester.ensureVisible(rejectButton);
    await tester.tap(rejectButton);
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRejectRequestSheet), findsOneWidget);
    expect(find.text('رفض طلب الزيارة'), findsOneWidget);

    await tester.tap(find.text('تأكيد الرفض'));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerVisitRequestsScreen), findsOneWidget);
    expect(find.byType(OwnerRejectRequestSheet), findsNothing);
    expect(find.text('تم الرفض'), findsOneWidget);
    expect(
      repository.lastApi,
      'properties/owner/visits/requests/sara-nasr-city/reject/',
    );
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, {
      'reason': 'timing_not_suitable',
      'custom_reason': '',
    });
    expect(tester.takeException(), isNull);
  });

  testWidgets('opens calendar with availability management for its property', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        OwnerVisitRequestsScreen(initialRequests: ownerVisitRequestsFixture()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('تقويم الزيارات'));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerRequestsCalendarScreen), findsOneWidget);
    expect(find.text('تقويم الزيارات'), findsOneWidget);
    expect(repository.lastApi, 'properties/owner/calendar/');
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastQuery, containsPair('year', DateTime.now().year));
    expect(repository.lastQuery, containsPair('month', DateTime.now().month));

    await tester.tap(find.text('19'));
    await tester.pumpAndSettle();
    expect(find.text('زيارات يوم 19'), findsOneWidget);
    expect(find.text('إدارة مواعيد الإتاحة'), findsOneWidget);
    expect(
      repository.requests.where((p) => p.api.contains('/availability/')),
      isEmpty,
    );
    expect(tester.takeException(), isNull);
  });
}

class _RecordingBaseRepository implements BaseRepository {
  final Map<int, Map<String, dynamic>> visitPages = {};
  bool visitsUnavailable = false;
  final List<CrudBaseParmas> requests = [];
  String lastApi = '';
  HttpRequestType? lastMethod;
  Map<String, dynamic>? lastBody;
  Map<String, dynamic>? lastQuery;
  String? lastCacheKey;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    lastApi = params.api;
    lastMethod = params.httpRequestType;
    lastBody = params.body;
    lastQuery = params.queryParameters;
    lastCacheKey = params.cacheKey;
    if (params.api == 'properties/owner/visits/requests/' ||
        params.api == 'properties/visits/received/') {
      if (visitsUnavailable) return Error(ServerFailure('Unavailable'));
      final response =
          visitPages[params.queryParameters?['page']] ??
          {'count': 0, 'next': null, 'results': const []};
      return Success(
        BaseModel<T>(key: '', msg: '', data: params.mapper!(response)),
      );
    }
    final List<String> pathParts = params.api.split('/');
    final dynamic response = params.api == 'chat/conversations/create/'
        ? {
            'id': 'owner-conversation',
            'other_participant': {
              'id': params.body?['user_id'] ?? 'tenant-id',
              'full_name': 'سارة أحمد خالد',
              'avatar': '',
              'is_online': false,
            },
            'last_message': null,
            'unread_count': 0,
            'created_at': '2026-09-15T00:00:00Z',
            'updated_at': '2026-09-15T00:00:00Z',
          }
        : params.httpRequestType == HttpRequestType.get &&
              pathParts.length > 5 &&
              pathParts[0] == 'properties' &&
              pathParts[1] == 'owner' &&
              pathParts[2] == 'visits' &&
              pathParts[3] == 'requests'
        ? _ownerRequestDetailsResponse(pathParts[4])
        : null;
    final T data = params.mapper!(response);
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _OwnerChatDataSource implements ChatDataSource {
  const _OwnerChatDataSource();

  @override
  String? get conversationsCacheKey => null;

  @override
  String? messagesCacheKey(String conversationId) => null;

  @override
  Future<(List<ConversationContent>, PaginationData)> getConversationsPage({
    required int page,
  }) async => (
    const <ConversationContent>[],
    PaginationData(perPage: 20, totalPages: 1),
  );

  @override
  Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = ChatData.conversationsPageSize,
  }) async {
    return ChatPageResponse<ConversationContent>(
      count: 0,
      next: null,
      previous: null,
      results: const [],
      page: page,
      pageSize: pageSize,
    );
  }

  @override
  Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  }) async => (
    const <ChatMessageContent>[],
    PaginationData(perPage: 50, totalPages: 1),
  );

  @override
  Future<ConversationContent> createConversation(String userId) async =>
      const ConversationContent.initial();

  @override
  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  }) async => const ChatMessageContent.initial();

  @override
  Future<ChatReadContent> markConversationAsRead(String conversationId) async =>
      const ChatReadContent(status: 'read');
}

class _OwnerTranslationsAssetLoader extends AssetLoader {
  const _OwnerTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    if (locale.languageCode == 'en') {
      return _ownerEnglishTranslations;
    }
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
