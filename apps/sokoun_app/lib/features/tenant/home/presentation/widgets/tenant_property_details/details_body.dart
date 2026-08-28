import 'package:flutter/material.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'bottom_actions.dart';
import 'details_content.dart';
import 'hero_gallery.dart';

class TenantPropertyDetailsBody extends StatelessWidget {
  const TenantPropertyDetailsBody({
    super.key,
    required this.property,
    required this.isSaved,
    required this.onBackPressed,
    required this.onSharePressed,
    required this.onSavedPressed,
    required this.onPhotosPressed,
    required this.onLocationPressed,
    required this.onBookVisitPressed,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback onBackPressed;
  final VoidCallback onSharePressed;
  final VoidCallback onSavedPressed;
  final ValueChanged<int> onPhotosPressed;
  final VoidCallback onLocationPressed;
  final VoidCallback onBookVisitPressed;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TenantPropertyHeroGallery(
                  property: property,
                  isSaved: isSaved,
                  onBackPressed: onBackPressed,
                  onSharePressed: onSharePressed,
                  onSavedPressed: onSavedPressed,
                  onPhotosPressed: onPhotosPressed,
                ),
                TenantPropertyDetailsContentView(
                  property: property,
                  onLocationPressed: onLocationPressed,
                ),
              ],
            ),
          ),
        ),
        TenantPropertyBottomActions(
          isSaved: isSaved,
          onBookVisitPressed: onBookVisitPressed,
          onSavedPressed: onSavedPressed,
        ),
      ],
    );
  }
}
