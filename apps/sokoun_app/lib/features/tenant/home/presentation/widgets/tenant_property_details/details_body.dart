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
    required this.onSavedPressed,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback onSavedPressed;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TenantPropertyHeroGallery(property: property),
                TenantPropertyDetailsContentView(property: property),
              ],
            ),
          ),
        ),
        TenantPropertyBottomActions(
          property: property,
          isSaved: isSaved,
          onSavedPressed: onSavedPressed,
        ),
      ],
    );
  }
}
