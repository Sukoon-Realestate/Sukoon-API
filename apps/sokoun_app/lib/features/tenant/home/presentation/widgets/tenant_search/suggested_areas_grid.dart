import 'package:flutter/material.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
    return Column(
      children: [
        Row(
          textDirection: TextDirection.ltr,
          children: [
            for (int index = 0; index < 3; index++) ...[
              Expanded(
                child: SuggestedAreaCard(
                  area: areas[index],
                  isSelected: areas[index].title == selectedArea,
                  onTap: onAreaSelected == null
                      ? null
                      : () => onAreaSelected!(areas[index]),
                ),
              ),
              if (index < 2) 10.szW,
            ],
          ],
        ),
        10.szH,
        Row(
          textDirection: TextDirection.ltr,
          children: [
            for (int index = 3; index < 6; index++) ...[
              Expanded(
                child: SuggestedAreaCard(
                  area: areas[index],
                  isSelected: areas[index].title == selectedArea,
                  onTap: onAreaSelected == null
                      ? null
                      : () => onAreaSelected!(areas[index]),
                ),
              ),
              if (index < 5) 10.szW,
            ],
          ],
        ),
      ],
    );
  }
}
