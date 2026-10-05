import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/upload_property_image_body.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class UploadPropertyImagesCubit extends AsyncCubit<List<PropertyImageModel>> {
  UploadPropertyImagesCubit() : super(const []);

  Future<void> uploadImages({
    required String propertyId,
    required List<OwnerPropertyPhotoDraft> photos,
    required void Function({
      required OwnerPropertyPhotoDraft photo,
      required PropertyImageModel image,
    })
    onPhotoUploaded,
    required void Function() onSuccess,
  }) async {
    if (isClosed || isLoading || propertyId.trim().isEmpty) return;
    final int generation = AccountSession.generation;
    await executeAsyncWithBaseModel(
      operation: () async {
        final results = await Future.wait(
          photos.where((photo) => !photo.isExisting).map((photo) async {
            final result = await baseCrudUseCase.call(
              CrudBaseParmas<PropertyImageModel>(
                api: ApiConstants.propertyImages(propertyId),
                httpRequestType: HttpRequestType.post,
                body: UploadPropertyImageBody(
                  image: photo.file,
                  name: photo.name,
                  description: photo.description,
                ).toJson(),
                isFromData: true,
                sendTimeout: ConstantManager.uploadSendTimeout,
                mapper: (json) {
                  final PropertyImageModel image = PropertyImageModel.fromJson(
                    json as Map<String, dynamic>,
                  );
                  if (image.id.trim().isEmpty || image.image.trim().isEmpty) {
                    throw const FormatException(
                      'Missing uploaded image ID or URL',
                    );
                  }
                  return image;
                },
              ),
            );
            final BaseModel<PropertyImageModel>? uploaded = result
                .tryGetSuccess();
            if (uploaded != null &&
                !isClosed &&
                generation == AccountSession.generation) {
              ObjectBoxCacheService.remove('property_details_$propertyId');
              ObjectBoxCacheService.remove('owner_properties');
              onPhotoUploaded(photo: photo, image: uploaded.data);
            }
            return result;
          }),
        );
        final List<PropertyImageModel> images = [];
        Failure? firstFailure;
        String message = '';
        for (final result in results) {
          result.when((model) {
            images.add(model.data);
            if (model.msg.isNotEmpty) message = model.msg;
          }, (failure) => firstFailure ??= failure);
        }
        final Failure? failure = firstFailure;
        if (failure != null) return Error(failure);
        return Success(BaseModel(key: '', msg: message, data: images));
      },
      onSuccess: (_) {
        ObjectBoxCacheService.remove('property_details_$propertyId');
        ObjectBoxCacheService.remove('owner_properties');
        onSuccess();
      },
    );
  }
}
