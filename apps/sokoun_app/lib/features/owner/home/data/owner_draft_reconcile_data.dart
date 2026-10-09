import 'models/owner_add_property_content.dart';
import 'models/owner_property_draft.dart';
import 'owner_add_property_mapper.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'dart:convert';

abstract final class OwnerDraftReconcileData {
  /// Image uploads may advance updated_at without changing the submitted form.
  /// Compare the acknowledged fields and image IDs before resuming only uploads.
  static bool matchesAcknowledged(
    PropertyDetailsModel previous,
    PropertyDetailsModel fresh,
  ) {
    final before = OwnerDraftFormCodec.encode(
      OwnerAddPropertyMapper.fromProperty(previous).form,
    );
    final now = OwnerDraftFormCodec.encode(
      OwnerAddPropertyMapper.fromProperty(fresh).form,
    );
    const ignored = {
      'photos',
      'submission_key',
      'selected_offer_ref',
      'option_labels',
    };
    if (before.keys.any(
      (field) =>
          !ignored.contains(field) &&
          jsonEncode(before[field]) != jsonEncode(now[field]),
    )) {
      return false;
    }
    final oldIds = {
      if (previous.mainImageId.isNotEmpty) previous.mainImageId,
      ...previous.images.map((image) => image.id).where((id) => id.isNotEmpty),
    };
    final freshIds = {
      if (fresh.mainImageId.isNotEmpty) fresh.mainImageId,
      ...fresh.images.map((image) => image.id).where((id) => id.isNotEmpty),
    };
    return oldIds.length == freshIds.length && oldIds.containsAll(freshIds);
  }

  static Set<String> dirtyFields(
    OwnerAddPropertyFormState draft,
    OwnerAddPropertyFormState? baseline,
  ) {
    final Map<String, dynamic> current = OwnerDraftFormCodec.encode(draft);
    final Map<String, dynamic> base = baseline == null
        ? {}
        : OwnerDraftFormCodec.encode(baseline);
    return {
      for (final String field in current.keys)
        if (jsonEncode(current[field]) != jsonEncode(base[field])) field,
    };
  }

  static OwnerAddPropertyFormState merge({
    required OwnerAddPropertyFormState draft,
    required PropertyDetailsModel fresh,
    required Set<String> dirtyFields,
  }) {
    final Map<String, dynamic> result = OwnerDraftFormCodec.encode(
      OwnerAddPropertyMapper.fromProperty(fresh).form,
    );
    final Map<String, dynamic> edits = OwnerDraftFormCodec.encode(draft);
    for (final String field in dirtyFields) {
      if (edits.containsKey(field)) result[field] = edits[field];
    }
    result['submission_key'] = draft.submissionKey;
    // Private files are never reconstructed from persisted JSON.
    return OwnerDraftFormCodec.decode(
      result,
    ).copyWith(ownershipProofFile: draft.ownershipProofFile);
  }
}
