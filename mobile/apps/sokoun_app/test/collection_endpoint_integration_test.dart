import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';

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
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/reviews/data/property_reviews_data.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/property_review.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_review_card.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/owner/visits/presentation/cubits/received_visits_cubit.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Repository repository;
  late _Network network;
  setUpAll(() async {
    const channel = MethodChannel('plugins.flutter.io/shared_preferences');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          channel,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    final font = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold']) {
      font.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await font.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
    for (final lang in ['ar', 'en']) {
      _translations[lang] =
          jsonDecode(
                await rootBundle.loadString(
                  'packages/melos_core/assets/translations/$lang.json',
                ),
              )
              as Map<String, dynamic>;
    }
  });
  setUp(() async {
    await injector.reset();
    repository = _Repository();
    network = _Network();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    injector.registerSingleton<NetworkService>(network);
  });
  tearDown(() => injector.reset());

  test(
    'maps collection visit details and preserves optional data through cache',
    () {
      final json = _example('/properties/visits/requests/{{visitId}}/');
      final details = TenantVisitDetailsContent.fromJson(json);
      expect(details.visit.propertyTitle, 'Cozy Studio Near Metro Station');
      expect(details.visit.day, json['day_label']);
      expect(details.visit.time, '9:00 ص');
      expect(details.visit.status.isPending, isTrue);
      expect(details.location, 'Maadi, Cairo');
      expect(details.bedrooms, 1);
      expect(details.note, "I'd like to inspect the apartment.");
      expect(details.visit.canCancel, isTrue);
      expect(details.visit.canChat, isFalse);
      expect(details.visit.canReview, isFalse);
      expect(TenantVisitDetailsContent.fromJson(details.toJson()), details);
      final sparse = TenantVisitDetailsContent.fromJson({
        'id': 'v',
        'status': 'pending',
      });
      expect(sparse.review, isNull);
      expect(sparse.bedrooms, isNull);
      expect(sparse.location, isEmpty);
    },
  );

  test('completed and canceled visits retain their server status', () {
    expect(
      TenantVisitContent.fromJson({'status': 'completed'}).status.isCompleted,
      isTrue,
    );
    expect(
      TenantVisitContent.fromJson({'status': 'canceled'}).status.isCanceled,
      isTrue,
    );
    final owner = OwnerVisitRequestContent.fromJson({
      'status': 'pending',
      'actions': {'can_accept': false, 'can_reject': true},
    });
    expect(owner.canAccept, isFalse);
    expect(owner.canReject, isTrue);
    expect(OwnerVisitRequestContent.fromJson(owner.toJson()), owner);
  });

  test('loads both tenant collection lists with distinct cache keys', () async {
    network.response = _example('/properties/visits/requests/?status=pending');
    final (visits, _) = await TenantVisitsData.getVisitsPage(
      page: 2,
      filter: TenantVisitFilter.pending,
      requests: true,
    );
    expect(network.request.path, 'properties/visits/requests/');
    expect(network.request.queryParameters, {'page': 2, 'status': 'pending'});
    expect(visits.first.propertyTitle, isNotEmpty);
    expect(visits.first.canReview, isFalse);
    await TenantVisitsData.getVisitsPage(
      page: 1,
      filter: TenantVisitFilter.all,
    );
    expect(network.request.path, 'properties/visits/');
    expect(
      TenantVisitsData.cacheKeyFor(TenantVisitFilter.all),
      isNot(
        TenantVisitsData.cacheKeyFor(TenantVisitFilter.all, requests: true),
      ),
    );
  });

  test('loads fresh details once while a request is pending', () async {
    repository.response = _example('/properties/visits/requests/{{visitId}}/');
    repository.gate = Completer<void>();
    final cubit = VisitDetailsCubit();
    addTearDown(cubit.close);
    final request = cubit.load('visit-id');
    await cubit.load('visit-id');
    expect(repository.requests, hasLength(1));
    expect(
      repository.requests.single.api,
      'properties/visits/requests/visit-id/',
    );
    expect(repository.requests.single.httpRequestType, HttpRequestType.get);
    repository.gate!.complete();
    await request;
    expect(cubit.data.note, isNotEmpty);
  });

  test(
    'cancellation submits once and does not report success before completion',
    () async {
      repository.gate = Completer<void>();
      final cubit = VisitCancelCubit();
      addTearDown(cubit.close);
      final request = cubit.cancel('visit-id');
      expect(await cubit.cancel('visit-id'), isFalse);
      expect(repository.requests, hasLength(1));
      expect(
        repository.requests.single.api,
        'properties/visits/visit-id/update/',
      );
      expect(repository.requests.single.httpRequestType, HttpRequestType.patch);
      expect(repository.requests.single.body, {'status': 'canceled'});
      expect(cubit.data, isFalse);
      repository.gate!.complete();
      expect(await request, isTrue);
    },
  );

  test(
    'review uses collection criteria and leaves overall rating to the server',
    () async {
      final cubit = VisitReviewCubit();
      addTearDown(cubit.close);
      expect(
        await cubit.submit(visitId: 'v', body: const VisitReviewBody.initial()),
        isFalse,
      );
      expect(repository.requests, isEmpty);
      expect(
        await cubit.submit(
          visitId: 'v',
          body: const VisitReviewBody(
            cleanliness: 4,
            accuracy: 5,
            ownerInteraction: 4,
            comment: ' Good visit ',
          ),
        ),
        isTrue,
      );
      final request = repository.requests.single;
      expect(request.api, 'properties/visits/v/review/');
      expect(request.httpRequestType, HttpRequestType.post);
      expect(request.body, {
        'cleanliness_rating': 4,
        'listing_accuracy_rating': 5,
        'owner_interaction_rating': 4,
        'comment': 'Good visit',
      });
    },
  );

  test(
    'property reviews use the property route and documented pagination',
    () async {
      network.response = _example('/properties/{{property_id}}/reviews/');
      final (reviews, pagination) = await PropertyReviewsData.getPage(
        propertyId: 'property-id',
        page: 1,
      );
      expect(network.request.path, 'properties/property-id/reviews/');
      expect(network.request.method, RequestMethod.get);
      expect(reviews.first.rating, 5);
      expect(reviews.first.name, isNotEmpty);
      expect(PropertyReview.fromJson(reviews.first.toJson()), reviews.first);
      expect(pagination.perPage, 10);
    },
  );

  test(
    'owner inbox and received list both use their collection routes',
    () async {
      repository.response = _example('/properties/owner/visits/requests/');
      final inbox = ReceivedVisitsCubit(requests: true);
      final received = ReceivedVisitsCubit();
      addTearDown(inbox.close);
      addTearDown(received.close);
      await inbox.getReceivedVisits();
      expect(repository.requests.last.api, 'properties/owner/visits/requests/');
      expect(inbox.data.first.dateLabel, 'النهارده 3م');
      await received.getReceivedVisits();
      expect(repository.requests.last.api, 'properties/visits/received/');
      final details = OwnerRequestDetailsCubit(useVisitEndpoint: true);
      addTearDown(details.close);
      await details.getRequestDetails('v');
      expect(repository.requests.last.api, 'properties/visits/v/');
    },
  );

  test(
    'editable profile loads server data and owner updates named fields',
    () async {
      repository.response = _example('/profiles/user/my-profile/');
      final cubit = UserProfileCubit();
      addTearDown(cubit.close);
      UserProfileContent? loaded;
      await cubit.load(onLoaded: (data) => loaded = data);
      expect(repository.requests.last.api, 'profiles/user/my-profile/');
      expect(loaded!.name, 'Mahmoud Salama');
      expect(
        loaded!
            .toUser(
              const UserModel(
                id: 'u',
                name: '',
                phone: '',
                email: 'kept@example.com',
              ),
            )
            .email,
        'kept@example.com',
      );
      final edit = ProfileEditCubit();
      addTearDown(edit.close);
      await edit.editProfile(
        updateUser: true,
        body: const ProfileEditBody(
          avatar: null,
          fullName: 'Mahmoud Salama',
          gender: 'male',
          phoneNumber: '01017595972',
        ),
        onSuccess: () {},
      );
      expect(repository.requests.last.api, 'profiles/user/update/');
      expect(repository.requests.last.httpRequestType, HttpRequestType.patch);
      expect(repository.requests.last.body, {
        'first_name': 'Mahmoud',
        'last_name': 'Salama',
        'gender': 'male',
        'phone_number': '01017595972',
      });
    },
  );

  test(
    'settings omit missing flags and PATCH only the changed preference',
    () async {
      repository.response = {
        'visit_notifications': true,
        'show_profile_in_search': false,
      };
      final cubit = ProfileSettingsCubit();
      final update = ProfileSettingUpdateCubit();
      addTearDown(cubit.close);
      addTearDown(update.close);
      await cubit.load();
      expect(repository.requests.last.api, 'profiles/settings/');
      expect(cubit.data.values.length, 2);
      expect(
        cubit.data.values.containsKey(ProfileSetting.shareLocation),
        isFalse,
      );
      expect(
        await update.save(ProfileSetting.visitNotifications, false),
        isTrue,
      );
      expect(repository.requests.last.httpRequestType, HttpRequestType.patch);
      expect(repository.requests.last.body, {'visit_notifications': false});
    },
  );

  test('explicit logout contacts the backend', () async {
    final cubit = ProfileLogoutCubit();
    addTearDown(cubit.close);
    expect(await cubit.logout(), isTrue);
    expect(repository.requests.single.api, 'auth/logout/');
    expect(repository.requests.single.httpRequestType, HttpRequestType.post);
    expect(ApiConstants.refreshToken, 'auth/refresh/');
    expect(ApiConstants.resetPassword, 'auth/users/reset_password/');
  });

  testWidgets('visit actions honor independent server permissions', (
    tester,
  ) async {
    final visit = TenantVisitContent.fromJson({
      'id': 'v',
      'status': 'completed',
      'owner': {'id': 'owner-id'},
      'actions': {
        'can_find_alternative': true,
        'can_chat': true,
        'can_review': true,
        'can_cancel': false,
      },
    });
    await tester.pumpWidget(
      _app(
        VisitDetailsActions(
          visit: visit,
          onReview: () async {},
          onCancel: () async {},
        ),
        'en',
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text(LocaleKeys.tenantVisitFindAlternative), findsOneWidget);
    expect(find.text(LocaleKeys.tenantVisitOpenOwnerChat), findsOneWidget);
    expect(find.text(LocaleKeys.tenantVisitRateAction), findsOneWidget);
    expect(find.text(LocaleKeys.tenantVisitCancelVisit), findsNothing);
  });

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
      testWidgets('visit extras are conditional and fit $locale at $width', (
        tester,
      ) async {
        tester.view.physicalSize = Size(width, 1100);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final json = _example('/properties/visits/requests/{{visitId}}/');
        json['review'] = {
          'overall_rating': 4.5,
          'comment': 'Existing review',
          'cleanliness_rating': 5,
        };
        final details = TenantVisitDetailsContent.fromJson(json);
        await tester.pumpWidget(
          _app(
            VisitDetailsContent(visit: details.visit, details: details),
            locale,
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Maadi, Cairo'), findsOneWidget);
        expect(find.text("I'd like to inspect the apartment."), findsOneWidget);
        expect(find.byType(PropertyReviewCard), findsOneWidget);
        if (width == 390 &&
            Platform.environment['CAPTURE_VISIT_DETAILS'] == '1') {
          final boundary = tester.renderObject<RenderRepaintBoundary>(
            find.byType(RepaintBoundary).first,
          );
          await tester.runAsync(() async {
            final ui.Image image = await boundary.toImage(pixelRatio: 1);
            final bytes = await image.toByteData(
              format: ui.ImageByteFormat.png,
            );
            await File(
              '/private/tmp/sokoun-visit-details-$locale.png',
            ).writeAsBytes(bytes!.buffer.asUint8List());
            image.dispose();
          });
        }
        expect(tester.takeException(), isNull);
        final sparse = TenantVisitDetailsContent.fromJson({
          'id': 'v',
          'status': 'pending',
        });
        await tester.pumpWidget(
          _app(
            VisitDetailsContent(visit: sparse.visit, details: sparse),
            locale,
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Maadi, Cairo'), findsNothing);
        expect(find.byType(PropertyReviewCard), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('a rejected mutation does not report success', (tester) async {
    await tester.pumpWidget(_app(const SizedBox(), 'en'));
    await tester.pumpAndSettle();
    repository.failure = const ServerFailure('Request rejected');
    final cancel = VisitCancelCubit();
    addTearDown(cancel.close);
    expect(await cancel.cancel('v'), isFalse);
    expect(cancel.state.isError, isTrue);
    final review = VisitReviewCubit();
    addTearDown(review.close);
    expect(
      await review.submit(
        visitId: 'v',
        body: const VisitReviewBody(
          cleanliness: 4,
          accuracy: 4,
          ownerInteraction: 4,
          comment: '',
        ),
      ),
      isFalse,
    );
    final logout = ProfileLogoutCubit();
    addTearDown(logout.close);
    expect(await logout.logout(), isFalse);
    await tester.pumpAndSettle();
    await tester.pump(const Duration(seconds: 5));
  });
}

Widget _app(Widget child, String language) => EasyLocalization(
  supportedLocales: const [Locale('ar'), Locale('en')],
  path: 'unused',
  assetLoader: const _Translations(),
  startLocale: Locale(language),
  saveLocale: false,
  child: ScreenUtilInit(
    designSize: const Size(390, 844),
    builder: (context, _) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      theme: ThemeData(scaffoldBackgroundColor: AppColors.scaffoldBackground),
      locale: context.locale,
      supportedLocales: context.supportedLocales,
      localizationsDelegates: context.localizationDelegates,
      home: Scaffold(
        body: MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(1.3)),
          child: child,
        ),
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

Map<String, dynamic> _example(String suffix) {
  final file = File('../../collection.json').existsSync()
      ? File('../../collection.json')
      : File('collection.json');
  final json = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  Map<String, dynamic>? result;
  void walk(List items) {
    for (final item in items.whereType<Map>()) {
      if (item['item'] is List) walk(item['item'] as List);
      final request = item['request'];
      if (request is! Map || request['url'] is! Map) continue;
      if (!(request['url']['raw'] as String? ?? '').endsWith(suffix)) continue;
      for (final response in (item['response'] as List? ?? [])) {
        if (response['body'] is! String) continue;
        final body =
            jsonDecode(response['body'] as String) as Map<String, dynamic>;
        if (body['data'] is Map) {
          result = Map<String, dynamic>.from(body['data'] as Map);
          return;
        }
      }
    }
  }

  walk(json['collection']['item'] as List);
  return result ?? (throw StateError('Missing collection example for $suffix'));
}

class _Repository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  dynamic response = <String, dynamic>{};
  Completer<void>? gate;
  Failure? failure;
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    await gate?.future;
    if (failure != null) return Error(failure!);
    return Success(
      BaseModel<T>(key: '', msg: '', data: params.mapper!(response)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _Network implements NetworkService {
  late NetworkRequest request;
  dynamic response = <String, dynamic>{};
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest networkRequest, {
    T Function(dynamic)? mapper,
  }) async {
    request = networkRequest;
    return BaseModel<T>(key: '', msg: '', data: mapper!(response));
  }

  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<bool> hasSessionCookies() async => true;
  @override
  Future<void> updateBaseUrl() async {}
}
