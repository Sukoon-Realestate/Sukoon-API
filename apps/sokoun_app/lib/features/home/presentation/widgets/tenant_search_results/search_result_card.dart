import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import 'amenity_row.dart';
import 'details_button.dart';
import 'result_image_header.dart';
import 'tags_row.dart';

class SearchResultCard extends StatelessWidget {
  const SearchResultCard({super.key, required this.item, this.onDetailsTap});

  final SearchResultContent item;
  final VoidCallback? onDetailsTap;

  @override
  Widget build(BuildContext context) {
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
          Padding(
            padding: EdgeInsets.all(14.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  item.title,
                  color: AppColors.sokoonNavy,
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                5.szH,
                Row(
                  children: [
                    Icon(
                      Icons.location_on_outlined,
                      color: AppColors.sokoonGray,
                      size: 15.r,
                    ),
                    4.szW,
                    Expanded(
                      child: AppText(
                        item.location,
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                9.szH,
                AmenityRow(item: item),
                10.szH,
                TagsRow(tags: item.tags),
                12.szH,
                Row(
                  textDirection: TextDirection.ltr,
                  children: [
                    DetailsButton(onTap: onDetailsTap),
                    const Spacer(),
                    Row(
                      children: [
                        AppText(
                          'ج/شهر',
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w400,
                        ),
                        5.szW,
                        AppText(
                          item.price,
                          color: AppColors.sokoonTeal,
                          fontSize: 18.sp,
                          fontWeight: FontWeight.w900,
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
