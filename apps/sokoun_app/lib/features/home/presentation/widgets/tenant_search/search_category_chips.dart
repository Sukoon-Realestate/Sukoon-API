import 'package:flutter/material.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

import 'search_chip.dart';

class SearchCategoryChips extends StatelessWidget {
  const SearchCategoryChips({super.key, required this.categories});

  final List<SearchCategoryContent> categories;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          for (int index = 0; index < categories.length; index++) ...[
            SearchChip(category: categories[index]),
            if (index < categories.length - 1) 8.szW,
          ],
        ],
      ),
    );
  }
}
