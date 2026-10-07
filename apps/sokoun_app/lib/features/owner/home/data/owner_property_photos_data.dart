import 'package:crypto/crypto.dart';
import 'package:equatable/equatable.dart';
import 'models/owner_add_property_content.dart';

class OwnerPropertyPhotoCheck extends Equatable {
  const OwnerPropertyPhotoCheck({this.photos = const []});
  const OwnerPropertyPhotoCheck.initial() : this();
  final List<OwnerPropertyPhotoDraft> photos;
  bool get hasDuplicates =>
      photos.map((photo) => photo.id).toSet().length != photos.length ||
      photos.map((photo) => photo.uniquenessKey).toSet().length !=
          photos.length;
  @override
  List<Object?> get props => [photos];
}

abstract final class OwnerPropertyPhotosData {
  /// Streams each local file so copies with different paths still count once.
  /// Remote content uniqueness is enforced by the upload/property service.
  static Future<OwnerPropertyPhotoCheck> check(
    List<OwnerPropertyPhotoDraft> photos,
  ) async {
    final checked = <OwnerPropertyPhotoDraft>[];
    for (final photo in photos) {
      final file = photo.file;
      if (file == null || photo.isExisting) {
        checked.add(photo);
        continue;
      }
      final fingerprint = (await sha256.bind(file.openRead()).first).toString();
      checked.add(
        fingerprint == photo.contentFingerprint
            ? photo
            : photo.copyWith(contentFingerprint: fingerprint),
      );
    }
    return OwnerPropertyPhotoCheck(photos: List.unmodifiable(checked));
  }
}
