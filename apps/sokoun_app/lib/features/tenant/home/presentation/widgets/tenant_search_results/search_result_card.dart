import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/sponsored_listing_badge.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/property_card_summary.dart';
import '../../screens/property_details_screen.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/property_filter_label_resolver.dart';

import 'amenity_row.dart';
import '../../../data/models/property_search_model.dart';
import 'details_button.dart';
import 'result_image_header.dart';
import 'tags_row.dart';

class SearchResultCard extends StatelessWidget {
  const SearchResultCard({
    super.key,
    required this.item,
    required this.filterOptions,
    this.preferences,
  });

  final PropertyDetailsModel item;
  final PropertyFilterOptionsModel filterOptions;
  final PropertySearchFilters? preferences;

  @override
  Widget build(BuildContext context) {
    final PropertyFilterLabelResolver labelResolver =
        PropertyFilterLabelResolver(filterOptions);
    final List<String> tags = [
      labelResolver.propertyTypeLabel(item.propertyType),
      if (item.suitableFor.isNotEmpty)
        labelResolver.suitableForLabel(item.suitableFor),
      if (item.isFurnished) LocaleKeys.tenantFilterFurnished,
      ...labelResolver.amenityLabels(item).take(2),
    ].where((label) => label.isNotEmpty).toList(growable: false);

    return Material(
      color: context.appColor(AppColors.white, surface: true),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.r),
        side: BorderSide(color: context.appColor(AppColors.grayPale)),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: item.id.isEmpty
            ? null
            : () => Go.to(
                PropertyDetailsScreen(
                  propertyId: item.id,
                  searchPreferences: preferences,
                ),
              ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ResultImageHeader(item: item),
            if (item.isSponsored)
              const SponsoredListingBadge()
                  .paddingSymmetric(horizontal: 14)
                  .paddingOnly(top: 12),
            PropertyCardSummary(
              title: item.title.isEmpty ? '••••••••••••' : item.title,
              location: [
                item.district,
                item.city.name,
              ].where((value) => value.isNotEmpty).join(', '),
              metadata: AmenityRow(item: item),
              tags: tags.isEmpty ? null : TagsRow(tags: tags),
              price: EgyptianPoundText.format(
                item.price,
                period: item.pricePeriod,
              ),
              action: DetailsButton(
                propertyId: item.id,
                preferences: preferences,
              ),
            ).paddingAll(14.w),
          ],
        ),
      ),
    );
  }
}
