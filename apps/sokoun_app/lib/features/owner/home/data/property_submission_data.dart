import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

import 'models/owner_add_property_content.dart';

abstract final class PropertySubmissionData {
  static CrudBaseParmas<PropertyDetailsModel> request({
    required OwnerAddPropertyFormState form,
    String? propertyId,
  }) {
    final bool isCreating = propertyId == null;
    return CrudBaseParmas<PropertyDetailsModel>(
      api: isCreating
          ? ApiConstants.createProperty
          : ApiConstants.propertyDetails(propertyId),
      httpRequestType: isCreating
          ? HttpRequestType.post
          : HttpRequestType.patch,
      body: form.toJson(includeMainImage: isCreating),
      isFromData: true,
      sendTimeout: ConstantManager.uploadSendTimeout,
      mapper: (json) {
        final property = json is Map<String, dynamic>
            ? PropertyDetailsModel.fromJson(json)
            : const PropertyDetailsModel.initial();
        if (isCreating && property.id.trim().isEmpty) {
          throw const FormatException('Missing created property ID');
        }
        return property;
      },
    );
  }
}
