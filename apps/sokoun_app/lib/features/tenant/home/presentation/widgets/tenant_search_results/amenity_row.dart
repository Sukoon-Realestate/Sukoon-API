import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

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
        if (item.bedrooms > 0)
          Amenity(
            icon: Icons.bed_outlined,
            label: !item.hasRentalOffers
                ? '${item.bedrooms} ${LocaleKeys.tenantSearchResultsBeds}'
                : LocaleKeys.rentalTotalRooms.replaceAll(
                    '{count}',
                    '${item.bedrooms}',
                  ),
          ),
        if (item.bathrooms > 0)
          Amenity(
            icon: Icons.shower_outlined,
            label: item.hasRentalOffers
                ? '${LocaleKeys.rentalParentPropertyBathrooms}: ${item.bathrooms}'
                : '${item.bathrooms} ${LocaleKeys.tenantSearchResultsBaths}',
          ),
        if (item.area > 0)
          Amenity(
            icon: Icons.square_foot_outlined,
            label: item.hasRentalOffers
                ? '${LocaleKeys.rentalParentPropertyArea}: ${item.area}'
                : '${item.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',
          ),
      ],
    );
  }
}
