import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_listing_content.dart';

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
            textDirection: TextDirection.ltr,
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
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.right,
                    ),
                    6.szH,
                    Align(
                      alignment: AlignmentDirectional.centerEnd,
                      child: OwnerListingStatusBadge(status: listing.status),
                    ),
                    8.szH,
                    AppText(
                      listing.price,
                      color: AppColors.sokoonTeal,
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.right,
                    ),
                    6.szH,
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AppText(
                          listing.views,
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w400,
                        ),
                        8.szW,
                        AppText(
                          '·',
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w400,
                        ),
                        8.szW,
                        AppText(
                          listing.visits,
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w400,
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
            textDirection: TextDirection.ltr,
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
