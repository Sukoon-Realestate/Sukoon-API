import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';

class AvailablePlacesCubit extends AsyncCubit<AvailablePlacesModel> {
  AvailablePlacesCubit() : super(const AvailablePlacesModel.initial());

  String? _propertyTypeId;
  Future<void>? _request;
  int _requestVersion = 0;
  CancelToken? _cancelToken;

  Future<void> retry() async {
    final String? propertyTypeId = _propertyTypeId;
    if (propertyTypeId == null) return;
    await getAvailablePlaces(propertyTypeId);
  }

  Future<void> getAvailablePlaces(String propertyTypeId) {
    if (isClosed) return Future<void>.value();
    if (_propertyTypeId == propertyTypeId && _request != null) return _request!;
    _propertyTypeId = propertyTypeId;
    _cancelToken?.cancel();
    final CancelToken cancelToken = _cancelToken = CancelToken();
    final int version = ++_requestVersion;
    return _request = _load(propertyTypeId, version, cancelToken).whenComplete(
      () {
        if (version == _requestVersion) _request = null;
      },
    );
  }

  Future<void> _load(
    String propertyTypeId,
    int version,
    CancelToken cancelToken,
  ) async {
    await executeAsyncWithBaseModel(
      shouldApplyResult: () => version == _requestVersion,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<AvailablePlacesModel>(
          api: ApiConstants.availablePlaces,
          httpRequestType: HttpRequestType.get,
          cancelToken: cancelToken,
          cacheKey: 'available_places_$propertyTypeId',
          queryParameters: {'property_type_id': propertyTypeId},
          mapper: (json) => AvailablePlacesModel.fromJson(json),
          fromCacheJson: AvailablePlacesModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  @override
  Future<void> close() {
    _requestVersion++;
    _cancelToken?.cancel();
    return super.close();
  }
}
