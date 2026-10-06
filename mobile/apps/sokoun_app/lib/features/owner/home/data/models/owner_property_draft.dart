import 'dart:io';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'owner_add_property_content.dart';
import 'property_location.dart';

class OwnerPropertyDraft extends Equatable {
  const OwnerPropertyDraft({
    this.form,
    this.savedProperty,
    this.isServerSnapshotCurrent = false,
    this.step = 0,
    this.savedAt,
    this.hasMissingFiles = false,
    this.localSaveFailed = false,
  });
  const OwnerPropertyDraft.initial()
    : form = null,
      savedProperty = null,
      isServerSnapshotCurrent = false,
      step = 0,
      savedAt = null,
      hasMissingFiles = false,
      localSaveFailed = false;
  factory OwnerPropertyDraft.fromJson(Map<String, dynamic> json) =>
      OwnerPropertyDraft(
        form: json['form'] is Map
            ? OwnerDraftFormCodec.decode(
                Map<String, dynamic>.from(json['form']),
              )
            : null,
        savedProperty: json['saved_property'] is Map
            ? PropertyDetailsModel.fromJson(
                Map<String, dynamic>.from(json['saved_property']),
              )
            : null,
        isServerSnapshotCurrent: json['server_snapshot_current'] == true,
        step: ((json['step'] as num?)?.toInt() ?? 0).clamp(0, 2),
        savedAt: DateTime.tryParse(json['saved_at']?.toString() ?? ''),
        hasMissingFiles: json['has_missing_files'] == true,
      );
  final OwnerAddPropertyFormState? form;
  final PropertyDetailsModel? savedProperty;
  final bool isServerSnapshotCurrent;
  final int step;
  final DateTime? savedAt;
  final bool hasMissingFiles;
  final bool localSaveFailed;
  Map<String, dynamic> toJson() => {
    'form': form == null ? null : OwnerDraftFormCodec.encode(form!),
    'saved_property': savedProperty?.toJson(),
    'server_snapshot_current': isServerSnapshotCurrent,
    'step': step,
    'saved_at': savedAt?.toIso8601String(),
    'has_missing_files': hasMissingFiles,
  };
  OwnerPropertyDraft copyWith({
    OwnerAddPropertyFormState? form,
    PropertyDetailsModel? savedProperty,
    bool? isServerSnapshotCurrent,
    int? step,
    DateTime? savedAt,
    bool? hasMissingFiles,
    bool? localSaveFailed,
  }) => OwnerPropertyDraft(
    form: form ?? this.form,
    savedProperty: savedProperty ?? this.savedProperty,
    isServerSnapshotCurrent:
        isServerSnapshotCurrent ?? this.isServerSnapshotCurrent,
    step: step ?? this.step,
    savedAt: savedAt ?? this.savedAt,
    hasMissingFiles: hasMissingFiles ?? this.hasMissingFiles,
    localSaveFailed: localSaveFailed ?? this.localSaveFailed,
  );
  @override
  List<Object?> get props => [
    form,
    savedProperty,
    isServerSnapshotCurrent,
    step,
    savedAt,
    hasMissingFiles,
    localSaveFailed,
  ];
}

/// Local draft encoding is deliberately separate from the multipart API body.
abstract final class OwnerDraftFormCodec {
  static File? _file(Object? value) =>
      value is String && value.isNotEmpty ? File(value) : null;
  static Map<String, dynamic> encode(OwnerAddPropertyFormState form) => {
    'title': form.title,
    'property_type': form.propertyType,
    'property_type_value': form.propertyTypeValue,
    'governorate_id': form.governorateId,
    'governorate': form.governorate,
    'district_id': form.districtId,
    'district': form.district,
    'street': form.street,
    'bedrooms': form.bedrooms,
    'bathrooms': form.bathrooms,
    'space': form.space,
    'floor': form.floor,
    'location': form.location?.toJson(),
    'photos': [
      for (final photo in form.photoDrafts)
        {
          'path': photo.file?.path,
          'id': photo.existingId,
          'url': photo.existingUrl,
          'name': photo.name,
          'description': photo.description,
        },
    ],
    'price': form.monthlyPrice,
    'rental_duration': form.rentalDuration,
    'rental_unit': form.rentalUnit,
    'amenities': form.amenities.toList(),
    'description': form.description,
    'suitable_for': form.suitableFor,
    'option_labels': form.optionLabels,
    'video_path': form.videoFile?.path,
    'video_url': form.videoUrl,
    'video_duration': form.videoDuration,
    'remove_video': form.removeVideo,
    'country': form.country,
    'area_description': form.areaDescription,
    'neighborhood': form.neighborhood,
    'building_year': form.buildingYear,
    'deposit': form.deposit,
    'smoking_allowed': form.smokingAllowed,
    'proof_path': form.ownershipProofFile?.path,
    'proof_url': form.ownershipProofUrl,
    'remove_proof': form.removeOwnershipProof,
  };
  static OwnerAddPropertyFormState decode(Map<String, dynamic> json) =>
      OwnerAddPropertyFormState(
        title: json['title'] as String? ?? '',
        propertyType: json['property_type'] as String? ?? '',
        propertyTypeValue: json['property_type_value'] as String? ?? '',
        governorateId: json['governorate_id'] as String? ?? '',
        governorate: json['governorate'] as String? ?? '',
        districtId: json['district_id'] as String? ?? '',
        district: json['district'] as String? ?? '',
        street: json['street'] as String? ?? '',
        bedrooms: json['bedrooms'] as String? ?? '',
        bathrooms: json['bathrooms'] as String? ?? '',
        space: json['space'] as String? ?? '',
        floor: json['floor'] as String? ?? '',
        location: json['location'] is Map
            ? PropertyLocation.fromJson(
                Map<String, dynamic>.from(json['location']),
              )
            : null,
        photoDrafts: (json['photos'] as List? ?? const [])
            .whereType<Map>()
            .map(
              (photo) => OwnerPropertyPhotoDraft(
                file: _file(photo['path']),
                existingId: photo['id'] as String? ?? '',
                existingUrl: photo['url'] as String? ?? '',
                name: photo['name'] as String? ?? '',
                description: photo['description'] as String? ?? '',
              ),
            )
            .toList(growable: false),
        monthlyPrice: json['price'] as String? ?? '',
        rentalDuration: json['rental_duration'] as String? ?? '',
        rentalUnit: json['rental_unit'] as String? ?? '',
        amenities: (json['amenities'] as List? ?? const [])
            .whereType<String>()
            .toSet(),
        description: json['description'] as String? ?? '',
        suitableFor: json['suitable_for'] as String? ?? '',
        optionLabels: Map<String, String>.from(
          json['option_labels'] as Map? ?? const {},
        ),
        videoFile: _file(json['video_path']),
        videoUrl: json['video_url'] as String? ?? '',
        videoDuration: (json['video_duration'] as num?)?.toInt(),
        removeVideo: json['remove_video'] == true,
        country: json['country'] as String? ?? 'Egypt',
        areaDescription: json['area_description'] as String? ?? '',
        neighborhood: json['neighborhood'] as String? ?? '',
        buildingYear: json['building_year'] as String? ?? '',
        deposit: json['deposit'] as String? ?? '',
        smokingAllowed: json['smoking_allowed'] as bool?,
        ownershipProofFile: _file(json['proof_path']),
        ownershipProofUrl: json['proof_url'] as String? ?? '',
        removeOwnershipProof: json['remove_proof'] == true,
      );
}
