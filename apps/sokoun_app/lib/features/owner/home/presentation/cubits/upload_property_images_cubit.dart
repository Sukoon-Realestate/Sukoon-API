import 'package:melos_core/core/network/network_request.dart';
import '../../data/models/property_upload_progress.dart';
import 'package:sokoun_app/features/main_view/data/account_access.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'dart:async';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/upload_property_image_body.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class UploadPropertyImagesCubit
    extends VerifiedActionCubit<List<PropertyImageModel>> {
  UploadPropertyImagesCubit() : super(const []);
  final CancelToken _cancel = CancelToken();
  final StreamController<Map<String, PropertyUploadProgress>> _progress =
      StreamController.broadcast();
  final Map<String, PropertyUploadProgress> _uploads = {};
  Stream<Map<String, PropertyUploadProgress>> get progress => _progress.stream;
  Map<String, PropertyUploadProgress> get uploads => Map.unmodifiable(_uploads);
  @override
  Future<void> close() async {
    _cancel.cancel();
    await _progress.close();
    await super.close();
  }

  Future<void> uploadImages({
    required String propertyId,
    required List<OwnerPropertyPhotoDraft> photos,
    required FutureOr<void> Function({
      required OwnerPropertyPhotoDraft photo,
      required PropertyImageModel image,
    })
    onPhotoUploaded,
    required void Function() onSuccess,
    Map<String, PropertyUploadProgress> restoredUploads = const {},
    Future<void> Function(Map<String, PropertyUploadProgress>)?
    onProgressChanged,
  }) async {
    if (isClosed || isLoading || propertyId.trim().isEmpty) return;
    final int generation = AccountSession.generation;
    await executeAsyncWithBaseModel(
      operation: () async {
        _uploads.addAll(restoredUploads);
        final pending = photos.where((photo) => !photo.isExisting).toList();
        final results = <Result<BaseModel<PropertyImageModel>, Failure>>[];
        int cursor = 0;
        bool stopped = false;
        Future<void> publish(
          PropertyUploadProgress progress, {
          bool persist = true,
        }) async {
          _uploads[progress.reference] = progress;
          if (!isClosed) _progress.add(uploads);
          if (persist) await onProgressChanged?.call(uploads);
        }

        final refs = photos.map((photo) => photo.reference).toSet();
        if (_uploads.values.any(
          (upload) =>
              !refs.contains(upload.reference) &&
              (upload.status == PropertyUploadStatus.sending ||
                  upload.status == PropertyUploadStatus.unknown),
        )) {
          return Error(ServerFailure(LocaleKeys.professionalUnknownOutcome));
        }
        _uploads.removeWhere((reference, _) => !refs.contains(reference));
        for (final photo in pending) {
          _uploads.putIfAbsent(
            photo.reference,
            () => PropertyUploadProgress(
              reference: photo.reference,
              status: PropertyUploadStatus.queued,
            ),
          );
        }
        if (!isClosed) _progress.add(uploads);
        await onProgressChanged?.call(uploads);

        Future<void> worker() async {
          while (!stopped &&
              cursor < pending.length &&
              !isClosed &&
              generation == AccountSession.generation) {
            final photo = pending[cursor++];
            if (_uploads[photo.reference]?.status ==
                PropertyUploadStatus.unknown) {
              results.add(
                Error(ServerFailure(LocaleKeys.professionalUnknownOutcome)),
              );
              stopped = true;
              return;
            }
            if (!AccountAccess.isVerified ||
                photo.file == null ||
                photo.needsReselection ||
                !await photo.file!.exists()) {
              results.add(
                Error(ServerFailure(LocaleKeys.freeDraftMissingFiles)),
              );
              stopped = true;
              return;
            }
            try {
              // Persist transmission intent first. Restart converts sending to unknown.
              await publish(
                PropertyUploadProgress(
                  reference: photo.reference,
                  status: PropertyUploadStatus.sending,
                ),
              );
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
                  cancelToken: _cancel,
                  sendTimeout: ConstantManager.uploadSendTimeout,
                  onSendProgress: (sent, total) {
                    if (isClosed || generation != AccountSession.generation) {
                      return;
                    }
                    unawaited(
                      publish(
                        PropertyUploadProgress(
                          reference: photo.reference,
                          status: PropertyUploadStatus.sending,
                          sent: sent,
                          total: total,
                        ),
                        persist: false,
                      ),
                    );
                  },
                  mapper: (json) {
                    final image = PropertyImageModel.fromJson(
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
              if (isClosed || generation != AccountSession.generation) return;
              final uploaded = result.tryGetSuccess();
              if (uploaded != null) {
                await onPhotoUploaded(photo: photo, image: uploaded.data);
                await publish(
                  PropertyUploadProgress(
                    reference: photo.reference,
                    status: PropertyUploadStatus.confirmed,
                    imageId: uploaded.data.id,
                  ),
                );
                ObjectBoxCacheService.remove('property_details_$propertyId');
                ObjectBoxCacheService.removePublicCollections();
              } else {
                final failure = result.tryGetError();
                final unknown =
                    failure?.outcomeUnknown == true ||
                    (failure?.statusCode == null &&
                        failure?.transport == null) ||
                    (failure?.statusCode ?? 0) >= 500;
                await publish(
                  PropertyUploadProgress(
                    reference: photo.reference,
                    status: unknown
                        ? PropertyUploadStatus.unknown
                        : PropertyUploadStatus.failed,
                  ),
                );
                if (unknown) stopped = true;
              }
              results.add(result);
            } catch (_) {
              stopped =
                  true; // Do not transmit further files after failed durable acknowledgment.
              results.add(Error(ServerFailure(LocaleKeys.freeLocalSaveFailed)));
            }
          }
        }

        await Future.wait([
          worker(),
          worker(),
        ]); // Explicit two-file concurrency budget.
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
