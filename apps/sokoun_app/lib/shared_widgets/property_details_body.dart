import 'package:flutter/material.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/details_body.dart';

typedef PropertyPhotosPressed =
    void Function(TenantPropertyDetailsContent property, int index);

class PropertyDetailsBody extends StatelessWidget {
  const PropertyDetailsBody({
    super.key,
    required this.property,
    required this.savedOverride,
    required this.onBackPressed,
    required this.onSharePressed,
    required this.onSavedPressed,
    required this.onPhotosPressed,
    required this.onLocationPressed,
    required this.onBookVisitPressed,
  });

  final TenantPropertyDetailsContent property;
  final bool? savedOverride;
  final VoidCallback onBackPressed;
  final ValueChanged<TenantPropertyDetailsContent> onSharePressed;
  final ValueChanged<TenantPropertyDetailsContent> onSavedPressed;
  final PropertyPhotosPressed onPhotosPressed;
  final ValueChanged<TenantPropertyDetailsContent> onLocationPressed;
  final ValueChanged<TenantPropertyDetailsContent> onBookVisitPressed;

  @override
  Widget build(BuildContext context) {
    return TenantPropertyDetailsBody(
      property: property,
      isSaved: savedOverride ?? property.isSaved,
      onBackPressed: onBackPressed,
      onSharePressed: () => onSharePressed(property),
      onSavedPressed: () => onSavedPressed(property),
      onPhotosPressed: (index) => onPhotosPressed(property, index),
      onLocationPressed: () => onLocationPressed(property),
      onBookVisitPressed: () => onBookVisitPressed(property),
    );
  }
}
