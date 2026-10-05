import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/lancher_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_rating_summary.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'amenity_wrap.dart';
import 'info_section.dart';
import 'metrics_grid.dart';
import 'owner_card.dart';
import 'ownership_verified_banner.dart';
import 'price.dart';
import 'tag_row.dart';
import 'property_description.dart';
import 'property_video.dart';
import 'rental_details.dart';
import 'listing_information.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

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
    return SokounReveal(
      key: ValueKey(property.id),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TenantPropertyTagRow(property: property),
          8.szH,
          AppText(
            property.title,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 19.sp,
            ),
            textAlign: TextAlign.start,
          ),
          8.szH,
          GestureDetector(
            onTap: _openLocation,
            behavior: HitTestBehavior.opaque,
            child: Row(
              spacing: 6.w,
              children: [
                Icon(
                  Icons.location_on_outlined,
                  color: context.appColor(AppColors.sokoonGray),
                  size: 18.r,
                ),
                Expanded(
                  child: AppText(
                    property.location,
                    style: AppTextStyles.medium13.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                    textAlign: TextAlign.start,
                  ),
                ),
              ],
            ),
          ),
          12.szH,
          TenantPropertyPrice(
            price: property.price,
            periodLabel: property.pricePeriodLabel,
          ),
          14.szH,
          TenantPropertyMetricsGrid(property: property),
          14.szH,
          TenantPropertyRentalDetails(property: property),
          14.szH,
          TenantPropertyListingInformation(property: property),
          if (property.videoUrl?.isNotEmpty ?? false) ...[
            14.szH,
            PropertyVideo(
              url: property.videoUrl!,
              durationSeconds: property.videoDuration,
            ),
          ],
          14.szH,
          TenantPropertyInfoSection(
            title: LocaleKeys.tenantPropertyDetailsDescription,
            child: PropertyDescription(description: property.description),
          ),
          12.szH,
          TenantPropertyInfoSection(
            title: LocaleKeys.tenantPropertyDetailsAmenities,
            child: TenantPropertyAmenityWrap(amenities: property.amenities),
          ),
          12.szH,
          if (property.id.isNotEmpty) ...[
            PropertyRatingSummary(propertyId: property.id),
            16.szH,
          ],
          if (property.isOwnershipVerified)
            const TenantPropertyOwnershipVerifiedBanner(),
          24.szH,
          TenantPropertyOwnerCard(property: property),
          28.szH,
        ],
      ),
    ).padding(EdgeInsets.fromLTRB(18.w, 16.h, 18.w, 20.h));
  }
}
