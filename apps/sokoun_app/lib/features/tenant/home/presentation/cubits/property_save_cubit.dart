import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

class PropertySaveCubit extends AsyncCubit<bool> {
  PropertySaveCubit() : super(false);

  Future<void> saveProperty({
    required String propertyId,
    required void Function(String msg) onError,
  }) async {
    await _updateSavedState(
      propertyId: propertyId,
      isSaved: true,
      onError: onError,
    );
  }

  Future<void> unsaveProperty({
    required String propertyId,
    required void Function(String msg) onError,
  }) async {
    await _updateSavedState(
      propertyId: propertyId,
      isSaved: false,
      onError: onError,
    );
  }

  Future<void> _updateSavedState({
    required String propertyId,
    required bool isSaved,
    required void Function(String msg) onError,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: isSaved
              ? ApiConstants.saveProperty(propertyId)
              : ApiConstants.unsaveProperty(propertyId),
          httpRequestType: isSaved
              ? HttpRequestType.post
              : HttpRequestType.delete,
          mapper: (_) => isSaved,
        ),
      ),
      onError: onError,
    );
  }
}
