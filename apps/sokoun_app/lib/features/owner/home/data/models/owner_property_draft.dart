import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'dart:io';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'owner_add_property_content.dart';
import 'property_location.dart';
import 'property_upload_progress.dart';

class OwnerPropertyDraft extends Equatable {
  const OwnerPropertyDraft({
    this.form,
    this.savedProperty,
    this.isServerSnapshotCurrent = false,
    this.serverFormConfirmed = false,
    this.step = 0,
    this.savedAt,
    this.hasMissingFiles = false,
    this.localSaveFailed = false,
    this.isSaving = false,
    this.baseRevision = '',
    this.needsPrivateDocument = false,
    this.unknownMutation = false,
    this.dirtyFields = const {},
    this.uploads = const {},
  });
  const OwnerPropertyDraft.initial()
    : form = null,
      savedProperty = null,
      isServerSnapshotCurrent = false,
      serverFormConfirmed = false,
      step = 0,
      savedAt = null,
      hasMissingFiles = false,
      localSaveFailed = false,
      isSaving = false,
      baseRevision = '',
      needsPrivateDocument = false,
      unknownMutation = false,
      dirtyFields = const {},
      uploads = const {};
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
        serverFormConfirmed: json['server_form_confirmed'] == true,
        step: ((json['step'] as num?)?.toInt() ?? 0).clamp(0, 2),
        savedAt: DateTime.tryParse(json['saved_at']?.toString() ?? ''),
        hasMissingFiles: json['has_missing_files'] == true,
        baseRevision: json['base_revision'] as String? ?? '',
        needsPrivateDocument: json['needs_private_document'] == true,
        unknownMutation: json['unknown_mutation'] == true,
        dirtyFields: (json['dirty_fields'] as List? ?? [])
            .whereType<String>()
            .toSet(),
        uploads: {
          for (final MapEntry entry in (json['uploads'] as Map? ?? {}).entries)
            entry.key.toString(): PropertyUploadProgress.fromJson(
              Map<String, dynamic>.from(entry.value as Map),
            ),
        },
      );
  final OwnerAddPropertyFormState? form;
  final PropertyDetailsModel? savedProperty;
  final bool isServerSnapshotCurrent;
  final bool serverFormConfirmed;
  final int step;
  final DateTime? savedAt;
  final bool hasMissingFiles;
  final bool localSaveFailed;
  final bool isSaving;
  final String baseRevision;
  final bool needsPrivateDocument;
  final bool unknownMutation;
  final Set<String> dirtyFields;
  final Map<String, PropertyUploadProgress> uploads;
  Map<String, dynamic> toJson() => {
    'form': form == null ? null : OwnerDraftFormCodec.encode(form!),
    'saved_property': savedProperty?.toJson(),
    'server_snapshot_current': isServerSnapshotCurrent,
    'server_form_confirmed': serverFormConfirmed,
    'step': step,
    'saved_at': savedAt?.toIso8601String(),
    'has_missing_files': hasMissingFiles,
    'base_revision': baseRevision,
    'needs_private_document': needsPrivateDocument,
    'unknown_mutation': unknownMutation,
    'dirty_fields': dirtyFields.toList(),
    'uploads': {
      for (final entry in uploads.entries) entry.key: entry.value.toJson(),
    },
  };
  OwnerPropertyDraft copyWith({
    OwnerAddPropertyFormState? form,
    PropertyDetailsModel? savedProperty,
    bool? isServerSnapshotCurrent,
    bool? serverFormConfirmed,
    int? step,
    DateTime? savedAt,
    bool? hasMissingFiles,
    bool? localSaveFailed,
    bool? isSaving,
    String? baseRevision,
    bool? needsPrivateDocument,
    bool? unknownMutation,
    Set<String>? dirtyFields,
    Map<String, PropertyUploadProgress>? uploads,
  }) => OwnerPropertyDraft(
    form: form ?? this.form,
    savedProperty: savedProperty ?? this.savedProperty,
    isServerSnapshotCurrent:
        isServerSnapshotCurrent ?? this.isServerSnapshotCurrent,
    serverFormConfirmed: serverFormConfirmed ?? this.serverFormConfirmed,
    step: step ?? this.step,
    savedAt: savedAt ?? this.savedAt,
    hasMissingFiles: hasMissingFiles ?? this.hasMissingFiles,
    localSaveFailed: localSaveFailed ?? this.localSaveFailed,
    isSaving: isSaving ?? this.isSaving,
    baseRevision: baseRevision ?? this.baseRevision,
    needsPrivateDocument: needsPrivateDocument ?? this.needsPrivateDocument,
    unknownMutation: unknownMutation ?? this.unknownMutation,
    dirtyFields: dirtyFields ?? this.dirtyFields,
    uploads: uploads ?? this.uploads,
  );
  @override
  List<Object?> get props => [
    form,
    savedProperty,
    isServerSnapshotCurrent,
    serverFormConfirmed,
    step,
    savedAt,
    hasMissingFiles,
    localSaveFailed,
    isSaving,
    baseRevision,
    needsPrivateDocument,
    unknownMutation,
    dirtyFields,
    uploads,
  ];
}

/// Local draft encoding is deliberately separate from the multipart API body.
abstract final class OwnerDraftFormCodec {
  static File? _file(Object? value) =>
      value is String && value.isNotEmpty ? File(value) : null;
  static Map<String, dynamic> encode(OwnerAddPropertyFormState form) => {
    'submission_key': form.submissionKey,
    'selected_offer_ref': form.selectedOfferRef,
    if (form.rentalInventory != null)
      'rental_inventory': form.rentalInventory!.toDraftJson(),
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
          'local_sha256': photo.contentFingerprint,
          'local_key': photo.draftKey,
          'needs_reselection': photo.needsReselection,
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
    'proof_url': form.ownershipProofUrl,
    'remove_proof': form.removeOwnershipProof,
  };
  static OwnerAddPropertyFormState decode(Map<String, dynamic> json) =>
      OwnerAddPropertyFormState(
        rentalInventory: json['rental_inventory'] is Map
            ? RentalInventory.fromDraftJson(
                Map<String, dynamic>.from(json['rental_inventory']),
              )
            : RentalInventory.read(json),
        selectedOfferRef: json['selected_offer_ref']?.toString() ?? '',
        submissionKey: json['submission_key']?.toString() ?? '',
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
                contentFingerprint: photo['local_sha256'] as String? ?? '',
                draftKey: photo['local_key'] as String? ?? '',
                needsReselection: photo['needs_reselection'] == true,
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
        ownershipProofUrl: json['proof_url'] as String? ?? '',
        removeOwnershipProof: json['remove_proof'] == true,
      );
}
