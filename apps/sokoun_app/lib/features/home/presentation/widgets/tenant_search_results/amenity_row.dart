import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/home/data/models/property_details_model.dart';

import 'amenity.dart';

class AmenityRow extends StatelessWidget {
  const AmenityRow({super.key, required this.item});

  final PropertyDetailsModel item;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14.w,
      runSpacing: 6.h,
      children: [
        Amenity(
          icon: Icons.bed_outlined,
          label: '${item.bedrooms} ${LocaleKeys.tenantSearchResultsBeds}',
        ),
        Amenity(
          icon: Icons.shower_outlined,
          label: '${item.bathrooms} ${LocaleKeys.tenantSearchResultsBaths}',
        ),
        Amenity(
          icon: Icons.square_foot_outlined,
          label: '${item.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',
        ),
      ],
    );
  }
}
