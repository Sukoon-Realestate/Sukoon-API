import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_listing_content.dart';

import 'owner_listing_action_button.dart';
import 'owner_listing_status_badge.dart';

class OwnerListingCard extends StatelessWidget {
  const OwnerListingCard({super.key, required this.listing});

  final OwnerListingContent listing;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: AppColors.sokoonBorder),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 80.r,
                height: 80.r,
                decoration: BoxDecoration(
                  color: AppColors.grayBluePale,
                  borderRadius: BorderRadius.circular(16.r),
                ),
                child: Icon(
                  listing.icon,
                  color: AppColors.blueGrayLight,
                  size: 28.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    AppText(
                      listing.title,
                      style: AppTextStyles.bold14.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.start,
                    ),
                    6.szH,
                    OwnerListingStatusBadge(status: listing.status).endWidget,
                    8.szH,
                    AppText(
                      listing.price,
                      style: AppTextStyles.bold16.copyWith(
                        color: AppColors.sokoonTeal,
                        fontSize: 16.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.start,
                    ),
                    6.szH,
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AppText(
                          listing.views,
                          style: AppTextStyles.regular12.copyWith(
                            color: AppColors.sokoonGray,
                            fontSize: 12.sp,
                            height: 1.45,
                          ),
                        ),
                        8.szW,
                        AppText(
                          '·',
                          style: AppTextStyles.regular12.copyWith(
                            color: AppColors.sokoonGray,
                            fontSize: 12.sp,
                            height: 1.45,
                          ),
                        ),
                        8.szW,
                        AppText(
                          listing.visits,
                          style: AppTextStyles.regular12.copyWith(
                            color: AppColors.sokoonGray,
                            fontSize: 12.sp,
                            height: 1.45,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          14.szH,
          Row(
            children: [
              for (
                int index = 0;
                index < OwnerListingsContent.actions.length;
                index++
              ) ...[
                OwnerListingActionButton(
                  action: OwnerListingsContent.actions[index],
                ),
                if (index < OwnerListingsContent.actions.length - 1) 8.szW,
              ],
            ],
          ),
        ],
      ),
    );
  }
}
