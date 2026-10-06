import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/visit_availability_content.dart';
import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _AvailabilityRepository repository;
  setUpAll(() async {
    for (final channel in [
      'dev.fluttercommunity.plus/connectivity',
      'dev.fluttercommunity.plus/connectivity_status',
    ]) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(
            MethodChannel(channel),
            (call) async => call.method == 'check' ? ['wifi'] : null,
          );
    }
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
  });
  setUp(() async {
    await injector.reset();
    repository = _AvailabilityRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });
  tearDown(() => injector.reset());

  test(
    'availability uses property and selected date with complete cache contracts',
    () async {
      final cubit = VisitAvailabilityCubit();
      await cubit.load('property-1', date: '2040-06-15');
      final request =
          repository.requests.single
              as CrudBaseParmas<VisitAvailabilityContent>;
      expect(request.api, ApiConstants.propertyAvailableDates('property-1'));
      expect(request.httpRequestType, HttpRequestType.get);
      expect(request.queryParameters, {'date': '2040-06-15'});
      expect(request.cacheKey, contains('property-1_2040-06-15'));
      expect(request.fromCacheJson, isNotNull);
      expect(request.toJson, isNotNull);
      expect(cubit.data.times.single.visitTime, '14:00:00');
      expect(cubit.data.times.single.isAvailable, isTrue);
      expect(
        VisitAvailabilityContent.fromJson(cubit.data.toJson()),
        cubit.data,
      );
      await cubit.close();
    },
  );

  testWidgets(
    'cached availability is explicitly marked and fresh reload clears the flag',
    (tester) async {
      await tester.pumpWidget(
        ScreenUtilInit(
          designSize: const Size(360, 690),
          builder: (_, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            home: const Scaffold(),
          ),
        ),
      );
      final cubit = VisitAvailabilityCubit();
      repository.fromCache = true;
      final cached = cubit.load('property', date: '2040-06-15');
      await tester.pumpAndSettle();
      await cached;
      expect(cubit.data.isCached, isTrue);
      repository.fromCache = false;
      final fresh = cubit.load('property', date: '2040-06-15');
      await tester.pumpAndSettle();
      await fresh;
      expect(cubit.data.isCached, isFalse);
      await cubit.close();
    },
  );

  test(
    'a late response for an older date cannot replace the selected date',
    () async {
      repository.oldDateGate = Completer<void>();
      final cubit = VisitAvailabilityCubit();
      final older = cubit.load('property', date: '2040-06-15');
      await pumpEventQueue();
      await cubit.load('property', date: '2040-06-16');
      expect(cubit.data.times.single.visitTime, '09:00:00');
      repository.oldDateGate!.complete();
      await older;
      expect(cubit.data.times.single.visitTime, '09:00:00');
      expect(cubit.state.isSuccess, isTrue);
      await cubit.close();
    },
  );

  test(
    'closing during an availability request suppresses its result',
    () async {
      repository.oldDateGate = Completer<void>();
      final cubit = VisitAvailabilityCubit();
      final pending = cubit.load('property', date: '2040-06-15');
      await pumpEventQueue();
      await cubit.close();
      repository.oldDateGate!.complete();
      await pending;
      expect(cubit.data.times, isEmpty);
    },
  );
}

class _AvailabilityRepository implements BaseRepository {
  final List<CrudBaseParmas<dynamic>> requests = [];
  bool fromCache = false;
  Completer<void>? oldDateGate;
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    final date = params.queryParameters?['date'];
    if (date == '2040-06-15') await oldDateGate?.future;
    final json = {
      'times': [
        {
          'time': '',
          'visit_time': date == '2040-06-16' ? '09:00:00' : '14:00:00',
          'is_available': true,
        },
      ],
    };
    return Success(
      BaseModel<T>(
        key: fromCache ? 'fromCache' : '',
        msg: '',
        data: params.mapper!(json),
      ),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
