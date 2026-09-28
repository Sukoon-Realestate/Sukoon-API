import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:gal/gal.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/shared/base_state.dart';

import '../../data/property_photo_gallery_data.dart';

typedef PropertyPhotoSaveState = ({BaseStatus status, String? errorMessage});

class PropertyPhotoSaveCubit extends Cubit<PropertyPhotoSaveState> {
  PropertyPhotoSaveCubit({PropertyPhotoGalleryData? galleryData})
    : _galleryData = galleryData ?? PropertyPhotoGalleryData(),
      super((status: BaseStatus.initial, errorMessage: null));

  final PropertyPhotoGalleryData _galleryData;

  String get _permissionDeniedMessage => LocaleKeys
      .tenantPropertyPhotoPermissionDenied
      .replaceAll('@album', PropertyPhotoGalleryData.albumName);

  Future<void> saveImage(String imageUrl) async {
    if (isClosed || state.status.isLoading) return;
    emit((status: BaseStatus.loading, errorMessage: null));

    try {
      final bool saved = await _galleryData.saveImage(imageUrl);
      emit((
        status: saved ? BaseStatus.success : BaseStatus.error,
        errorMessage: saved ? null : _permissionDeniedMessage,
      ));
    } on GalException catch (error) {
      emit((
        status: BaseStatus.error,
        errorMessage: switch (error.type) {
          GalExceptionType.accessDenied => _permissionDeniedMessage,
          GalExceptionType.notEnoughSpace =>
            LocaleKeys.tenantPropertyPhotoStorageFull,
          GalExceptionType.notSupportedFormat =>
            LocaleKeys.tenantPropertyPhotoUnsupportedFormat,
          GalExceptionType.unexpected =>
            LocaleKeys.tenantPropertyPhotoSaveFailed,
        },
      ));
    } catch (_) {
      emit((
        status: BaseStatus.error,
        errorMessage: LocaleKeys.tenantPropertyPhotoSaveFailed,
      ));
    }
  }

  @override
  void emit(PropertyPhotoSaveState state) {
    if (isClosed) return;
    super.emit(state);
  }
}
