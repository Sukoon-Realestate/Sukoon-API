import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/validators.dart';

import '../../../data/enums/property_price_period.dart';
import '../../../data/models/owner_add_property_content.dart';

/// The same rules are used by the fields and the step's first-error list.
class PropertyFormValidation {
  static String? photos(OwnerAddPropertyFormState form) =>
      form.hasDuplicatePhotos
      ? LocaleKeys.rentalDuplicatePhotos
      : Validators.isValidPropertyPhotos(count: form.photoCount)
      ? null
      : form.photoCount < OwnerAddPropertyContent.minimumPhotoCount
      ? LocaleKeys.ownerAddPropertyPhotosRemaining.replaceAll(
          '{count}',
          '${OwnerAddPropertyContent.minimumPhotoCount - form.photoCount}',
        )
      : LocaleKeys.ownerAddPropertyPhotoTipLimits;

  static String? video(OwnerAddPropertyFormState form) {
    if (form.isVideoPreparing) return LocaleKeys.ownerPropertyVideoPreparing;
    if (!form.hasVideo || form.removeVideo) {
      return LocaleKeys.ownerPropertyVideoRequired;
    }
    if (form.videoFile != null || form.videoDuration != null) {
      return Validators.validatePropertyVideoDuration(
        Duration(seconds: form.videoDuration ?? 0),
      );
    }
    return null;
  }

  static String? positiveInteger(String? value) {
    if (value == null || value.trim().isEmpty) return LocaleKeys.fillField;
    return Validators.isPositiveInteger(value)
        ? null
        : LocaleKeys.propertyPositiveNumber;
  }

  static String? floor(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    return Validators.isInteger(value) ? null : LocaleKeys.validationInteger;
  }

  static String? price(String? value) =>
      Validators.isPositiveNumber(value ?? '')
      ? null
      : LocaleKeys.propertyPositiveNumber;

  static String? rentalDuration(String? value) =>
      Validators.isPositiveInteger(value ?? '')
      ? null
      : LocaleKeys.propertyPositiveNumber;

  static String? rentalUnit(String? value) =>
      PropertyPricePeriod.fromValue(value ?? '') != null
      ? null
      : LocaleKeys.fillField;

  static String? description(String? value) =>
      Validators.hasMinimumLength(value ?? '', 10)
      ? null
      : LocaleKeys.propertyDescriptionMinimum;

  static String? buildingYear(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final int? year = int.tryParse(value);
    return year != null && year >= 1800 && year <= DateTime.now().year
        ? null
        : LocaleKeys.ownerAddPropertyBuildingYearInvalid;
  }
}
