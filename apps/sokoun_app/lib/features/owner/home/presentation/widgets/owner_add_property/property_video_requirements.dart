import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import 'add_property_section_card.dart';

class VideoRequirementsCard extends StatelessWidget {
  const VideoRequirementsCard({super.key});

  @override
  Widget build(BuildContext context) {
    final List<String> requirements = [
      LocaleKeys.ownerPropertyVideoRequirementDuration,
      LocaleKeys.ownerPropertyVideoRequirementRooms,
      LocaleKeys.ownerPropertyVideoRequirementStable,
      LocaleKeys.ownerPropertyVideoRequirementPrivacy,
    ];

    return AddPropertySectionCard(
      title: LocaleKeys.ownerPropertyVideoRequirements,
      child: Column(
        children: [
          for (int index = 0; index < requirements.length; index++) ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.check_rounded,
                  color: AppColors.sokoonTeal,
                  size: 16.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    requirements[index],
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w400,
                    textAlign: TextAlign.start,
                    maxLines: 2,
                  ),
                ),
              ],
            ),
            if (index < requirements.length - 1) ...[
              8.szH,
              const Divider(height: 1, color: AppColors.sokoonBorder),
              8.szH,
            ],
          ],
          12.szH,
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 9.h),
            decoration: BoxDecoration(
              color: AppColors.orangePale,
              borderRadius: BorderRadius.circular(10.r),
              border: Border.all(color: AppColors.goldAlpha15),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.schedule_rounded,
                  color: AppColors.brown,
                  size: 16.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    LocaleKeys.ownerPropertyVideoMaximumDuration,
                    color: AppColors.brown,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w700,
                    textAlign: TextAlign.start,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
