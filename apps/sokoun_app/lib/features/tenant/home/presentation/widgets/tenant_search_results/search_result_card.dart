import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/property_filter_label_resolver.dart';

import 'amenity_row.dart';
import 'details_button.dart';
import 'result_image_header.dart';
import 'tags_row.dart';

class SearchResultCard extends StatelessWidget {
  const SearchResultCard({
    super.key,
    required this.item,
    required this.filterOptions,
  });

  final PropertyDetailsModel item;
  final PropertyFilterOptionsModel filterOptions;

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

    return Container(
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.grayPale),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ResultImageHeader(item: item),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                item.title.isEmpty ? '••••••••••••' : item.title,
                style: AppTextStyles.bold15.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 15.sp,
                  height: 1.45,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              5.szH,
              Row(
                spacing: 4.w,
                children: [
                  Icon(
                    Icons.location_on_outlined,
                    color: AppColors.sokoonGray,
                    size: 15.r,
                  ),
                  Expanded(
                    child: AppText(
                      item.id.isEmpty
                          ? '••••••••••••'
                          : [
                              item.district,
                              item.city.name,
                            ].where((value) => value.isNotEmpty).join(', '),
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              9.szH,
              AmenityRow(item: item),
              10.szH,
              TagsRow(tags: tags),
              12.szH,
              Wrap(
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 12.w,
                runSpacing: 8.h,
                children: [
                  AppText(
                    EgyptianPoundText.format(
                      item.price,
                      period: item.pricePeriod,
                    ),
                    style: AppTextStyles.bold.copyWith(
                      color: AppColors.sokoonTeal,
                      fontSize: 18.sp,
                    ),
                  ),
                  DetailsButton(propertyId: item.id),
                ],
              ),
            ],
          ).paddingAll(14.w),
        ],
      ),
    );
  }
}
