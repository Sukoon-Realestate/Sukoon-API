import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/base_crud/code/data/base_data_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/extensions/error_handler_extension.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';

void main() {
  test(
    'CRUD copy and remote forwarding preserve controls and cache serializers',
    () async {
      final token = CancelToken();
      void progress(int sent, int total) {}
      final params = CrudBaseParmas<Map<String, dynamic>>(
        api: 'file/',
        httpRequestType: HttpRequestType.get,
        cacheKey: 'file-cache',
        mapper: (json) => json as Map<String, dynamic>,
        fromCacheJson: (json) => json,
        toJson: (json) => json,
        cancelToken: token,
        sendTimeout: const Duration(seconds: 7),
        onSendProgress: progress,
        onReceiveProgress: progress,
      );
      final copied = params.copyWith(api: 'other/');
      expect(copied.cacheKey, params.cacheKey);
      expect(copied.fromCacheJson, same(params.fromCacheJson));
      expect(copied.toJson, same(params.toJson));
      final network = _Network();
      await BaseRemoteDataSourceImpl(dioService: network).crudCall(copied);
      expect(network.request.path, 'other/');
      expect(network.request.cancelToken, same(token));
      expect(network.request.sendTimeout, const Duration(seconds: 7));
      expect(network.request.onSendProgress, same(progress));
      expect(network.request.onReceiveProgress, same(progress));
      final cloned = network.request.copyWith(path: 'third/');
      expect(cloned.cancelToken, same(token));
      expect(cloned.onReceiveProgress, same(progress));
      expect(
        NetworkRequest.fromJson(cloned.toJson()).sendTimeout,
        cloned.sendTimeout,
      );
    },
  );

  test('cancelled cached reads never read or write the cache', () async {
    final result =
        await Future<BaseModel<Map<String, dynamic>>>.error(
          const RequestCancelledException(),
        ).handleCallbackWithCache(
          cacheKey: 'cancelled',
          fromCacheJson: (json) => json,
          toJson: (json) => json,
          onSave: (_, __) => fail('Cancelled requests must not write cache'),
          onRead: (_) =>
              throw TestFailure('Cancelled requests must not read cache'),
        );
    expect(result.tryGetError(), isA<RequestCancelledFailure>());
    final uncached = await Future<void>.error(
      const RequestCancelledException(),
    ).handleCallbackWithFailure();
    expect(uncached.tryGetError(), isA<RequestCancelledFailure>());
  });
}

class _Network implements NetworkService {
  late NetworkRequest request;
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest networkRequest, {
    T Function(dynamic)? mapper,
  }) async {
    request = networkRequest;
    return BaseModel(key: '', msg: '', data: mapper!(<String, dynamic>{}));
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
