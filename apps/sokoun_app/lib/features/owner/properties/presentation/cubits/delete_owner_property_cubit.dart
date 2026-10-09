import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import '../../data/models/owner_property_deletion_model.dart';

class DeleteOwnerPropertyCubit
    extends VerifiedActionCubit<OwnerPropertyDeletionModel> {
  DeleteOwnerPropertyCubit()
    : super(const OwnerPropertyDeletionModel.initial());

  Future<void> delete({
    required String propertyId,
    required void Function() onSuccess,
  }) async {
    if (isClosed || isLoading || propertyId.trim().isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerPropertyDeletionModel>(
          api: ApiConstants.deleteProperty(propertyId),
          httpRequestType: HttpRequestType.delete,
          mapper: (json) => OwnerPropertyDeletionModel.fromJson(
            Map<String, dynamic>.from(json as Map),
          ),
        ),
      ),
      onSuccess: (model) {
        if (!model.data.confirms(propertyId)) {
          setError(errorMessage: model.msg);
          return;
        }
        ObjectBoxCacheService.removePublicCollections();
        ObjectBoxCacheService.remove('property_details_$propertyId');
        ObjectBoxCacheService.remove('owner_properties');
        ObjectBoxCacheService.remove('owner_dashboard');
        if (model.msg.isNotEmpty) {
          Messages.showToast(msg: model.msg, status: BaseStatus.success);
        }
        onSuccess();
      },
    );
  }
}
