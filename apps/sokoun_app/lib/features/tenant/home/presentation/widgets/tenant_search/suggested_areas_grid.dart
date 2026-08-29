import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';

import 'suggested_area_card.dart';

class SuggestedAreasGrid extends StatelessWidget {
  const SuggestedAreasGrid({
    super.key,
    required this.areas,
    this.selectedArea,
    this.onAreaSelected,
  });

  final List<SuggestedAreaContent> areas;
  final String? selectedArea;
  final ValueChanged<SuggestedAreaContent>? onAreaSelected;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: .82,
        crossAxisSpacing: 10.w,
        mainAxisSpacing: 10.h,
      ),
      itemCount: areas.length,
      itemBuilder: (context, index) {
        final SuggestedAreaContent area = areas[index];
        return SuggestedAreaCard(
          area: area,
          isSelected: area.searchQuery == selectedArea,
          onTap: onAreaSelected == null ? null : () => onAreaSelected!(area),
        );
      },
    );
  }
}
