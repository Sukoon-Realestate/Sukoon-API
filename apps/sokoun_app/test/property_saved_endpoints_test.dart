import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'helpers/account_test_dependencies.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorites_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _FakeNetworkService networkService;
  late _RecordingBaseRepository repository;

  setUpAll(CacheStorage.init);
  setUp(() async {
    await injector.reset();
    await registerAuthenticatedTestAccount();
    networkService = _FakeNetworkService();
    repository = _RecordingBaseRepository();
    injector
      ..registerSingleton<NetworkService>(networkService)
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      );
  });

  tearDown(() => injector.reset());

  test('loads and maps the saved properties page', () async {
    final response = await FavoritesData.getSavedProperties(page: 2);

    expect(networkService.lastRequest.path, ApiConstants.savedProperties);
    expect(networkService.lastRequest.method, RequestMethod.get);
    expect(networkService.lastRequest.queryParameters, {'page': 2});
    expect(response.count, 1);
    expect(response.perPage, 9);
    expect(response.totalPages, 1);
    expect(response.results.single.id, 'fbcc6585-3ab8-465d-9893-9d5c648817d5');
    expect(response.results.single.mainImage, startsWith('https://'));
    expect(response.results.single.isSaved, isTrue);
  });

  test('uses POST to save and DELETE to unsave a property', () async {
    final PropertySaveCubit cubit = PropertySaveCubit();
    addTearDown(cubit.close);

    await cubit.saveProperty(
      propertyId: 'property-id',
      onError: (msg) => fail(msg),
    );
    expect(repository.lastApi, 'properties/property-id/save/');
    expect(repository.lastMethod, HttpRequestType.post);

    await cubit.unsaveProperty(
      propertyId: 'property-id',
      onError: (msg) => fail(msg),
    );
    expect(repository.lastApi, 'properties/property-id/unsave/');
    expect(repository.lastMethod, HttpRequestType.delete);
  });
}

class _FakeNetworkService implements NetworkService {
  late NetworkRequest lastRequest;

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    lastRequest = networkRequest;
    final Model data = mapper!(const {
      'count': 1,
      'per_page': 9,
      'total_pages': 1,
      'results': [
        {
          'id': 'fbcc6585-3ab8-465d-9893-9d5c648817d5',
          'main_image': 'https://example.com/property.webp',
          'title': 'Cozy Studio Near Metro Station',
          'property_type': 'studio',
          'is_furnished': true,
          'bedrooms': 1,
          'bathrooms': 1,
          'area': 55,
          'price': '7000.00',
          'price_period': 'monthly',
          'rating': 0,
          'saved_at': '2026-08-29T21:16:58.716390+03:00',
          'is_saved': true,
        },
      ],
    });
    return BaseModel<Model>(key: '', msg: '', data: data);
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => false;

  @override
  Future<void> updateBaseUrl() async {}
}

class _RecordingBaseRepository implements BaseRepository {
  String lastApi = '';
  HttpRequestType? lastMethod;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    lastApi = params.api;
    lastMethod = params.httpRequestType;
    final T data = params.mapper!(null);
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
