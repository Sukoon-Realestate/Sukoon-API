import 'package:sokoun_app/features/shared/unread_counts/data/models/unread_counts.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/network/network_logging_policy.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/main_view/data/models/workspace_counts.dart';
import 'package:sokoun_app/features/shared/auth/data/models/complete_registration_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/complete_registration_cubit.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_pending_screen.dart';
import 'package:sokoun_app/features/shared/public_pages/data/enums/public_page.dart';
import 'package:sokoun_app/features/shared/public_pages/data/models/public_page_content.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/cubits/public_page_cubit.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/screens/public_page_screen.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/widgets/public_page_empty_state.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/my_review.dart';
import 'package:sokoun_app/features/shared/reviews/data/my_reviews_data.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/screens/my_reviews_screen.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/my_reviews_empty_state.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/my_review_card.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/share_sheet.dart';
import 'helpers/account_test_dependencies.dart';

final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const preferences = MethodChannel('plugins.flutter.io/shared_preferences');
  late _BackendRepository repository;
  late _ReviewsNetwork network;
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    const connectivity = MethodChannel(
      'dev.fluttercommunity.plus/connectivity',
    );
    const connectivityStatus = MethodChannel(
      'dev.fluttercommunity.plus/connectivity_status',
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          connectivity,
          (call) async => call.method == 'check' ? <String>['wifi'] : null,
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityStatus, (_) async => null);
    EasyLocalization.logger.enableBuildModes = [];
    await CacheStorage.init();
    for (final language in ['en', 'ar']) {
      _translations[language] =
          jsonDecode(
                await rootBundle.loadString(
                  'packages/melos_core/assets/translations/$language.json',
                ),
              )
              as Map<String, dynamic>;
    }
  });
  setUp(() async {
    await injector.reset();
    repository = _BackendRepository();
    network = _ReviewsNetwork();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    injector.registerSingleton<NetworkService>(network);
  });
  tearDown(() async {
    AccountSession.end();
    await CacheStorage.delete('user');
    await injector.reset();
  });

  test('video and canonical property links survive cache round trips', () {
    final model = PropertyDetailsModel.fromJson({
      'id': 'property-1',
      'video': 'https://cdn.example.com/tour.mp4',
      'video_duration': 45,
      'property_link': 'https://sokoun.app/properties/property-1',
    });
    expect(PropertyDetailsModel.fromJson(model.toJson()), model);
    expect(model.copyWith(title: 'Updated').videoDuration, 45);
    final content = TenantPropertyDetailsContent.fromModel(model);
    expect(content.videoUrl, 'https://cdn.example.com/tour.mp4');
    expect(content.shareUrl, 'https://sokoun.app/properties/property-1');
    final absent = PropertyDetailsModel.fromJson({
      'id': 'property-2',
      'video': null,
      'video_duration': null,
    });
    expect(absent.video, isNull);
    expect(absent.videoDuration, isNull);
    expect(
      TenantPropertyDetailsContent.fromModel(absent).shareUrl,
      'https://sokoun.app/properties/property-2',
    );
  });

  testWidgets('share uses the canonical link and a native popover origin', (
    tester,
  ) async {
    _phone(tester);
    const channel = MethodChannel('dev.fluttercommunity.plus/share');
    MethodCall? shared;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          shared = call;
          return 'com.example.shareTarget';
        });
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null),
    );
    const link = 'https://sokoun.app/properties/property-1';
    await tester.pumpWidget(
      _app(const Scaffold(body: TenantPropertyShareSheet(shareUrl: link))),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text(LocaleKeys.tenantPropertyDetailsShare));
    await tester.pumpAndSettle();
    expect(shared?.method, 'share');
    expect(shared?.arguments['uri'], link);
    expect(shared?.arguments['originWidth'], greaterThan(0));
    expect(shared?.arguments['originHeight'], greaterThan(0));
    expect(tester.takeException(), isNull);
  });

  test('counts use account totals instead of conversation pagination', () {
    const json = {
      'favorites_count': 145,
      'visit_requests_count': 8,
      'unread_chat_messages_count': 240,
      'unread_notifications_count': 12,
    };
    final counts = WorkspaceCounts.fromJson(json);
    expect(counts.favorites, 145);
    expect(counts.visits, 8);
    expect(WorkspaceCounts.fromJson(counts.toJson()), counts);
    expect(UnreadCounts.fromJson(json).chatCount, 240);
    expect(UnreadCounts.fromJson(json).notificationsCount, 12);
  });

  test('formatted visit time takes precedence over the machine value', () {
    final visit = OwnerVisitRequestContent.fromJson({
      'id': 'visit-1',
      'time': '02:30 PM',
      'visit_time': '14:30:00',
    });
    expect(visit.time, '02:30 PM');
    expect(OwnerVisitRequestContent.fromJson(visit.toJson()), visit);
  });

  test('identity uploads and session credentials stay out of diagnostics', () {
    expect(
      NetworkLoggingPolicy.isSensitive(ApiConstants.completeRegister),
      isTrue,
    );
    expect(
      NetworkLoggingPolicy.isSensitive(ApiConstants.tenantUnreadCounts),
      isFalse,
    );
    expect(
      NetworkLoggingPolicy.safeHeaders({
        'Authorization': 'Bearer secret',
        'Cookie': 'access_token=secret',
        'set-cookie': ['refresh_token=secret'],
        'Accept': 'application/json',
      }),
      {
        'Authorization': '[redacted]',
        'Cookie': '[redacted]',
        'set-cookie': '[redacted]',
        'Accept': 'application/json',
      },
    );
  });

  test(
    'both workspace count endpoints are reachable by the same account',
    () async {
      await registerAuthenticatedTestAccount();
      for (final workspace in AppWorkspace.values) {
        final cubit = UnreadCountsCubit();
        await cubit.load(workspace: workspace);
        expect(
          repository.lastParams?.api,
          workspace.isOwner
              ? ApiConstants.ownerUnreadCounts
              : ApiConstants.tenantUnreadCounts,
        );
        expect(
          cubit.data.forWorkspace(workspace).visits,
          workspace.isOwner ? 4 : 2,
        );
        await cubit.close();
      }
    },
  );

  test(
    'existing KYC sends only supplied fields and never registration credentials',
    () async {
      final body = KycUploadDocumentsData(backIdImage: File('/test/back.jpg'));
      expect(body.toJson().keys, ['back_id_image']);
      final cubit = CompleteRegistrationCubit();
      CompleteRegistrationResult? result;
      await cubit.submit(body, onResult: (value) => result = value);
      expect(repository.lastParams?.api, ApiConstants.completeRegister);
      expect(repository.lastParams?.httpRequestType, HttpRequestType.post);
      expect(repository.lastParams?.isFromData, isTrue);
      expect(repository.lastParams?.cacheKey, isNull);
      expect(result?.isComplete, isFalse);
      expect(result?.missingFields, ['back_id_image']);
      expect(CompleteRegistrationResult.fromJson(result!.toJson()), result);
      await cubit.close();
    },
  );

  test('KYC success requires complete flag and no missing fields', () {
    expect(
      CompleteRegistrationResult.fromJson({
        'registration_complete': false,
      }).isComplete,
      isFalse,
    );
    expect(
      CompleteRegistrationResult.fromJson({
        'registration_complete': true,
        'missing_fields': ['national_id'],
      }).isComplete,
      isFalse,
    );
    expect(
      CompleteRegistrationResult.fromJson({
        'registration_complete': true,
        'missing_fields': [],
        'verification_status': 'pending',
      }).isComplete,
      isTrue,
    );
  });

  test(
    'KYC prevents duplicate submissions and ignores a disposed result',
    () async {
      final gate = Completer<void>();
      repository.gate = gate;
      final cubit = CompleteRegistrationCubit();
      int results = 0;
      final first = cubit.submit(
        const KycUploadDocumentsData(),
        onResult: (_) => results++,
      );
      await cubit.submit(
        const KycUploadDocumentsData(),
        onResult: (_) => results++,
      );
      expect(repository.calls, 1);
      await cubit.close();
      gate.complete();
      await first;
      expect(results, 0);
    },
  );

  test(
    'public content uses explicit language and distinct cache keys',
    () async {
      final cubit = PublicPageCubit();
      for (final page in PublicPage.values) {
        for (final language in ['en', 'ar']) {
          await cubit.load(page: page, language: language);
          final params =
              repository.lastParams! as CrudBaseParmas<PublicPageContent>;
          expect(params.api, page.endpoint);
          expect(params.queryParameters, {'lang': language});
          expect(params.cacheKey, 'public_page_${page.name}_$language');
          expect(params.fromCacheJson!(params.toJson!(cubit.data)), cubit.data);
        }
      }
      await cubit.close();
    },
  );

  test(
    'reviews support both documented pagination shapes and cache mapping',
    () async {
      final review = MyReview.fromJson(_review);
      expect(MyReview.fromJson(review.toJson()), review);
      final standard = MyReviewsData.parsePage({
        'per_page': 10,
        'total_pages': 3,
        'results': [_review],
      }, page: 1);
      expect(standard.$2.totalPages, 3);
      final counted = MyReviewsData.parsePage({
        'count': 21,
        'next': 'https://api.example.com/?page=2',
        'results': [_review],
      }, page: 1);
      expect(counted.$2.totalPages, 3);
      expect(
        MyReviewsData.parsePage({'count': 0, 'results': []}, page: 1).$1,
        isEmpty,
      );
      await MyReviewsData.getPage(2);
      expect(network.lastRequest?.path, ApiConstants.myRates);
      expect(network.lastRequest?.queryParameters, {
        'page': 2,
        'page_size': 10,
      });
    },
  );

  testWidgets(
    'partial KYC stays on form and successful completion keeps the signed-in journey',
    (tester) async {
      _phone(tester);
      await registerAuthenticatedTestAccount();
      await tester.pumpWidget(
        _app(const KycUploadDocumentsScreen(existingAccount: true)),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.nextReviewData));
      await tester.pumpAndSettle();
      expect(
        find.text('${LocaleKeys.kycMissingFields}: ${LocaleKeys.idBackLabel}'),
        findsOneWidget,
      );
      expect(find.byType(KycPendingScreen), findsNothing);
      repository.kycResponse = {
        'registration_complete': true,
        'missing_fields': [],
        'verification_status': 'pending',
      };
      await tester.tap(find.text(LocaleKeys.nextReviewData));
      await tester.pumpAndSettle();
      expect(find.byType(KycPendingScreen), findsOneWidget);
      expect(
        tester
            .widget<KycPendingScreen>(find.byType(KycPendingScreen))
            .existingAccount,
        isTrue,
      );
      expect(AccountSession.userId, '1');
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('public empty success renders its contextual state', (
    tester,
  ) async {
    _phone(tester);
    repository.pageContent = '';
    await tester.pumpWidget(
      _app(const PublicPageScreen(page: PublicPage.aboutUs)),
    );
    await tester.pumpAndSettle();
    expect(find.byType(PublicPageEmptyState), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('reviews empty success renders its contextual state', (
    tester,
  ) async {
    _phone(tester);
    await tester.pumpWidget(_app(const MyReviewsScreen()));
    await tester.pumpAndSettle();
    expect(find.byType(MyReviewsEmptyState), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('public failure is not empty and retry restores real content', (
    tester,
  ) async {
    _phone(tester);
    repository.fail = true;
    await tester.pumpWidget(
      _app(const PublicPageScreen(page: PublicPage.privacy)),
    );
    await tester.pumpAndSettle();
    expect(find.byType(ExceptionView), findsOneWidget);
    expect(find.text('Request failed'), findsOneWidget);
    expect(find.byType(PublicPageEmptyState), findsNothing);
    repository.fail = false;
    await tester.tap(find.text(LocaleKeys.ownerRetryAction));
    await tester.pumpAndSettle();
    expect(find.text(repository.pageContent), findsOneWidget);
    expect(find.byType(ExceptionView), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('reviews failure offers retry without showing an empty success', (
    tester,
  ) async {
    _phone(tester);
    network.fail = true;
    await tester.pumpWidget(_app(const MyReviewsScreen()));
    await tester.pumpAndSettle();
    expect(find.byType(ExceptionView), findsOneWidget);
    expect(find.text('Request failed'), findsOneWidget);
    expect(find.byType(MyReviewsEmptyState), findsNothing);
    network.fail = false;
    network.reviews = [_review];
    await tester.tap(find.text(LocaleKeys.ownerRetryAction));
    await tester.pumpAndSettle();
    expect(find.byType(MyReviewCard), findsOneWidget);
    expect(find.byType(ExceptionView), findsNothing);
    expect(tester.takeException(), isNull);
  });
}

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Widget _app(Widget home) => EasyLocalization(
  supportedLocales: const [Locale('en'), Locale('ar')],
  path: 'packages/melos_core/assets/translations',
  startLocale: const Locale('en'),
  saveLocale: false,
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    enableScaleWH: () => false,
    enableScaleText: () => false,
    builder: (context, _) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      navigatorObservers: [AppNavigationObserver.instance],
      locale: context.locale,
      supportedLocales: context.supportedLocales,
      localizationsDelegates: context.localizationDelegates,
      home: MediaQuery(
        data: const MediaQueryData(
          size: Size(390, 844),
          disableAnimations: true,
        ),
        child: home,
      ),
    ),
  ),
);

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations[locale.languageCode]!;
}

class _BackendRepository implements BaseRepository {
  CrudBaseParmas<dynamic>? lastParams;
  int calls = 0;
  bool fail = false;
  Completer<void>? gate;
  String pageContent = 'Backend page content';
  Map<String, dynamic> kycResponse = {
    'registration_complete': false,
    'verification_status': 'pending',
    'missing_fields': ['back_id_image'],
  };
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    lastParams = params;
    calls++;
    await gate?.future;
    if (fail) return const Error(ServerFailure('Request failed'));
    final Map<String, dynamic> json;
    if (params.api == ApiConstants.completeRegister) {
      json = kycResponse;
    } else if (params.api == ApiConstants.ownerUnreadCounts) {
      json = {'visit_requests_count': 4};
    } else if (params.api == ApiConstants.tenantUnreadCounts) {
      json = {'favorites_count': 6, 'visit_requests_count': 2};
    } else {
      json = {
        'slug': 'about-us',
        'title': 'Sokoun',
        'content': pageContent,
        'content_format': 'plain_text',
        'language': params.queryParameters?['lang'] ?? 'en',
      };
    }
    return Success(BaseModel<T>(key: '', msg: '', data: params.mapper!(json)));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _ReviewsNetwork implements NetworkService {
  NetworkRequest? lastRequest;
  bool fail = false;
  List<Map<String, dynamic>> reviews = [];
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) async {
    lastRequest = request;
    if (fail) throw const ServerException('Request failed');
    return BaseModel<T>(
      key: '',
      msg: '',
      data: mapper!({'per_page': 10, 'total_pages': 1, 'results': reviews}),
    );
  }

  @override
  Future<bool> hasSessionCookies() async => true;
  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<void> updateBaseUrl() async {}
}

const _review = {
  'id': 'review-1',
  'property_id': 'property-1',
  'property_title': 'Apartment',
  'property_image': null,
  'visit_id': 'visit-1',
  'rating': 5,
  'comment': 'Accurate listing',
  'created_at': '2026-09-28T14:13:00Z',
};
