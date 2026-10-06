import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter/material.dart';
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
        spacing: 8.w,
        children: [
          for (int index = 0; index < propertyTypes.length; index++)
            SearchChip(
              label: propertyTypes[index].name,
              isSelected: propertyTypes[index].slug == selectedCategory,
              onTap: onCategorySelected == null
                  ? null
                  : () => onCategorySelected?.call(propertyTypes[index]),
            ),
        ],
      ),
    );
  }
}
