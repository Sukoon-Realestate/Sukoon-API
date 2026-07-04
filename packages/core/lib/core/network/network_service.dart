import '../base_crud/code/domain/usecases/pagination_response.dart';
import 'network_request.dart';

abstract interface class NetworkService {
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  });

  void setToken(String token);

  void removeToken();
  Future<void> updateBaseUrl();
}
