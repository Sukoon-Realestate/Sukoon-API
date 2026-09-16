import 'package:flutter/material.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';

import 'search_chip.dart';

class SearchCategoryChips extends StatelessWidget {
  const SearchCategoryChips({
    super.key,
    required this.propertyTypes,
    required this.selectedCategory,
    this.onCategorySelected,
  });

  final List<PropertyTypeModel> propertyTypes;
  final String selectedCategory;
  final ValueChanged<PropertyTypeModel>? onCategorySelected;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (int index = 0; index < propertyTypes.length; index++) ...[
            SearchChip(
              label: propertyTypes[index].name,
              isSelected: propertyTypes[index].slug == selectedCategory,
              onTap: onCategorySelected == null
                  ? null
                  : () => onCategorySelected?.call(propertyTypes[index]),
            ),
            if (index < propertyTypes.length - 1) 8.szW,
          ],
        ],
      ),
    );
  }
}
