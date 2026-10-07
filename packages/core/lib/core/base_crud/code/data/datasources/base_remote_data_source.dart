part of '../base_data_imports.dart';

abstract class BaseRemoteDataSource {
  Future<List<T>> getData<T extends BaseEntity>(GetBaseEntityParams? param);

  Future<BaseModel<T>> crudCall<T>(CrudBaseParmas<T> param);
}

@LazySingleton(as: BaseRemoteDataSource)
class BaseRemoteDataSourceImpl implements BaseRemoteDataSource {
  final NetworkService dioService;

  BaseRemoteDataSourceImpl({required this.dioService});
  @override
  Future<List<T>> getData<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) async {
    return (await dioService.callApi<List<T>>(
      NetworkRequest(
        path: getBaseIdAndNameEntityApi<T>(param),
        queryParameters: param?.toJson(),
        method: RequestMethod.get,
      ),
      mapper: (json) => param?.mapper != null
          ? param!.mapper!<List<T>>(json)
          : List<T>.from(json.map((x) => baseIdAndNameEntityFromJson<T>(x))),
    )).data;
  }

  @override
  Future<BaseModel<T>> crudCall<T>(CrudBaseParmas<T> param) async {
    final response = await dioService.callApi<T>(
      NetworkRequest(
        path: param.api,
        method: param.httpRequestType.requestMethod,
        body: param.body,
        isFormData: param.isFromData,
        queryParameters: param.queryParameters,
        headers: param.headers,
        onSendProgress: param.onSendProgress,
        onReceiveProgress: param.onReceiveProgress,
        cancelToken: param.cancelToken,
        sendTimeout: param.sendTimeout,
      ),
      mapper: param.mapper,
    );

    return response;
  }
}
