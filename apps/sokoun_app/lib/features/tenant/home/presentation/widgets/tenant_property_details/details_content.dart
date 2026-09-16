import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/lancher_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'amenity_wrap.dart';
import 'info_section.dart';
import 'metrics_grid.dart';
import 'owner_card.dart';
import 'ownership_verified_banner.dart';
import 'price_and_rating.dart';
import 'tag_row.dart';

class TenantPropertyDetailsContentView extends StatelessWidget {
  const TenantPropertyDetailsContentView({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  Future<void> _openLocation() async {
    await LauncherHelper.launchGoogleMaps(
      latitude: property.latitude,
      longitude: property.longitude,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TenantPropertyTagRow(property: property),
        8.szH,
        AppText(
          property.title,
          color: AppColors.sokoonNavy,
          fontSize: 19.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.start,
          maxLines: 2,
        ),
        8.szH,
        GestureDetector(
          onTap: _openLocation,
          behavior: HitTestBehavior.opaque,
          child: Row(
            children: [
              Icon(
                Icons.location_on_outlined,
                color: AppColors.sokoonGray,
                size: 18.r,
              ),
              6.szW,
              Expanded(
                child: AppText(
                  property.location,
                  color: AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w500,
                  textAlign: TextAlign.start,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        12.szH,
        TenantPropertyPriceAndRating(property: property),
        14.szH,
        TenantPropertyMetricsGrid(property: property),
        14.szH,
        TenantPropertyInfoSection(
          title: LocaleKeys.tenantPropertyDetailsDescription,
          child: AppText(
            property.description,
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            fontWeight: FontWeight.w500,
            height: 1.45,
            textAlign: TextAlign.start,
          ),
        ),
        12.szH,
        TenantPropertyInfoSection(
          title: LocaleKeys.tenantPropertyDetailsAmenities,
          child: TenantPropertyAmenityWrap(amenities: property.amenities),
        ),
        12.szH,
        const TenantPropertyOwnershipVerifiedBanner(),
        24.szH,
        TenantPropertyOwnerCard(property: property),
        28.szH,
      ],
    ).padding(EdgeInsets.fromLTRB(18.w, 16.h, 18.w, 20.h));
  }
}
