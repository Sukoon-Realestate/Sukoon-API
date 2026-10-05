import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

class DeleteOwnerPropertyCubit extends AsyncCubit<bool> {
  DeleteOwnerPropertyCubit() : super(false);

  Future<void> delete({
    required String propertyId,
    required void Function() onSuccess,
  }) async {
    if (isClosed || isLoading || propertyId.trim().isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.deleteProperty(propertyId),
          httpRequestType: HttpRequestType.delete,
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) {
        ObjectBoxCacheService.remove('property_details_$propertyId');
        ObjectBoxCacheService.remove('owner_properties');
        ObjectBoxCacheService.remove('owner_dashboard');
        onSuccess();
      },
    );
  }
}
