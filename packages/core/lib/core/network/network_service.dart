import '../base_crud/code/domain/usecases/pagination_response.dart';
import 'network_request.dart';

abstract interface class NetworkService {
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  });

  Future<bool> hasSessionCookies();

  Future<void> clearSessionCookies();

  Future<void> updateBaseUrl();
}
