import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

class CreatePropertyCubit extends AsyncCubit<Map<String, dynamic>> {
  CreatePropertyCubit() : super(const {});

  Future<void> createProperty({
    required OwnerAddPropertyFormState form,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.createProperty,
          httpRequestType: HttpRequestType.post,
          body: form.toRequestBody(),
          isFromData: true,
          mapper: (json) =>
              json is Map<String, dynamic> ? json : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
