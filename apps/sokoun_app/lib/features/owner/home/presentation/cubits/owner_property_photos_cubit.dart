import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import '../../data/models/owner_add_property_content.dart';
import '../../data/owner_property_photos_data.dart';

class OwnerPropertyPhotosCubit
    extends VerifiedActionCubit<OwnerPropertyPhotoCheck> {
  OwnerPropertyPhotosCubit() : super(const OwnerPropertyPhotoCheck.initial());

  Future<OwnerPropertyPhotoCheck?> check(
    List<OwnerPropertyPhotoDraft> photos,
  ) async {
    if (isClosed || isLoading) return null;
    OwnerPropertyPhotoCheck? checked;
    await executeAsyncWithBaseModel(
      operation: () async {
        try {
          final result = await OwnerPropertyPhotosData.check(photos);
          return Success(BaseModel(key: 'success', msg: '', data: result));
        } catch (_) {
          return Error(ServerFailure(LocaleKeys.rentalPhotosCheckFailed));
        }
      },
      onSuccess: (model) => checked = model.data,
    );
    return isClosed ? null : checked;
  }
}
