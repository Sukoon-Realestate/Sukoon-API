import 'package:flutter/material.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

import 'suggested_area_card.dart';

class SuggestedAreasGrid extends StatelessWidget {
  const SuggestedAreasGrid({super.key, required this.areas});

  final List<SuggestedAreaContent> areas;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          textDirection: TextDirection.ltr,
          children: [
            for (int index = 0; index < 3; index++) ...[
              Expanded(child: SuggestedAreaCard(area: areas[index])),
              if (index < 2) 10.szW,
            ],
          ],
        ),
        10.szH,
        Row(
          textDirection: TextDirection.ltr,
          children: [
            for (int index = 3; index < 6; index++) ...[
              Expanded(child: SuggestedAreaCard(area: areas[index])),
              if (index < 5) 10.szW,
            ],
          ],
        ),
      ],
    );
  }
}
