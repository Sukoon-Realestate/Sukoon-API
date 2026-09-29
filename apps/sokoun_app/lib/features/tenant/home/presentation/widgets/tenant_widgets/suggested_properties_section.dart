import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'home_property_item.dart';
import 'tenant_suggested_properties_empty_state.dart';

class SuggestedPropertiesSection extends StatelessWidget {
  const SuggestedPropertiesSection({super.key, required this.properties});
  final List<HomePropertyModel> properties;
  @override
  Widget build(BuildContext context) => properties.isEmpty
      ? const TenantSuggestedPropertiesEmptyState()
      : SokounAdaptiveGrid(
          children: [
            for (final property in properties)
              HomePropertyItem(property: property),
          ],
        );
}
