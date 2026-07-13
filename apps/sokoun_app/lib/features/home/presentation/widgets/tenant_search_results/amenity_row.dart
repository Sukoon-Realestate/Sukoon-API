import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import 'amenity.dart';

class AmenityRow extends StatelessWidget {
  const AmenityRow({super.key, required this.item});

  final SearchResultContent item;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14.w,
      runSpacing: 6.h,
      children: [
        Amenity(icon: Icons.bed_outlined, label: item.rooms),
        Amenity(icon: Icons.shower_outlined, label: item.bathrooms),
        Amenity(icon: Icons.square_foot_outlined, label: item.area),
      ],
    );
  }
}
