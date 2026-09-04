import 'package:flutter/material.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/details_body.dart';

class PropertyDetailsBody extends StatelessWidget {
  const PropertyDetailsBody({
    super.key,
    required this.property,
    required this.savedOverride,
    required this.onSavedPressed,
  });

  final TenantPropertyDetailsContent property;
  final bool? savedOverride;
  final ValueChanged<TenantPropertyDetailsContent> onSavedPressed;

  @override
  Widget build(BuildContext context) {
    return TenantPropertyDetailsBody(
      property: property,
      isSaved: savedOverride ?? property.isSaved,
      onSavedPressed: () => onSavedPressed(property),
    );
  }
}
