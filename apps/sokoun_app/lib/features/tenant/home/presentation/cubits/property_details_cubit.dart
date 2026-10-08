import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class PropertyDetailsCubit extends AsyncCubit<PropertyDetailsModel> {
  PropertyDetailsCubit() : super(const PropertyDetailsModel.initial());
  Future<void>? _loadRequest;

  Future<void> getPropertyDetails(String id) =>
      _loadRequest ??= _load(id).whenComplete(() => _loadRequest = null);

  Future<void> refresh(String id) async {
    await _loadRequest;
    if (!isClosed) await getPropertyDetails(id);
  }

  Future<void> _load(String id) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(id),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'property_details_$id',
          mapper: (json) => PropertyDetailsModel.fromJson(json),
          fromCacheJson: PropertyDetailsModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
