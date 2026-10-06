import 'package:easy_localization/easy_localization.dart' hide TextDirection;
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import '../../data/models/property_review.dart';

class PropertyReviewCard extends StatelessWidget {
  const PropertyReviewCard({super.key, required this.review});
  final PropertyReview review;
  @override
  Widget build(BuildContext context) {
    final DateTime? date = DateTime.tryParse(review.createdAt);
    final rows = <({String label, double? value})>[
      (
        label: LocaleKeys.tenantVisitRatingCleanliness,
        value: review.cleanliness,
      ),
      (label: LocaleKeys.tenantVisitRatingAccuracy, value: review.accuracy),
      (
        label: LocaleKeys.tenantVisitRatingOwnerTreatment,
        value: review.ownerInteraction,
      ),
    ];
    return Container(
      margin: EdgeInsets.symmetric(vertical: 6.h),
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 8.h,
        children: [
          if (review.name.isNotEmpty || review.avatarUrl.isNotEmpty)
            Row(
              spacing: 10.w,
              children: [
                if (review.avatarUrl.trim().isNotEmpty)
                  ExcludeSemantics(
                    child: CachedImage(
                      url: review.avatarUrl,
                      width: 40.r,
                      height: 40.r,
                      fit: BoxFit.cover,
                      boxShape: BoxShape.circle,
                      bgColor: context.appColor(
                        AppColors.bluePale,
                        surface: true,
                      ),
                      placeHolder: Icon(
                        Icons.person_outline_rounded,
                        color: context.appColor(AppColors.sokoonGray),
                      ),
                    ),
                  ),
                Expanded(
                  child: AppText(review.name, style: AppTextStyles.bold14),
                ),
              ],
            ),
          if (review.isVerified)
            AppText(LocaleKeys.verified, style: AppTextStyles.regular12),
          if (review.rating != null)
            Wrap(
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 4.w,
              children: [
                Icon(
                  Icons.star_rounded,
                  color: context.appColor(AppColors.amber),
                ),
                Directionality(
                  textDirection: TextDirection.ltr,
                  child: AppText(
                    '${review.rating!.toStringAsFixed(1)} / 5',
                    style: AppTextStyles.bold16.copyWith(
                      color: context.appColor(AppColors.amber),
                    ),
                  ),
                ),
              ],
            ),
          for (final row in rows)
            if (row.value != null)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 8.w,
                children: [
                  Expanded(
                    child: AppText(row.label, style: AppTextStyles.regular13),
                  ),
                  Directionality(
                    textDirection: TextDirection.ltr,
                    child: AppText(
                      '${row.value!.toStringAsFixed(1)} / 5',
                      style: AppTextStyles.regular13,
                    ),
                  ),
                ],
              ),
          if (review.comment.isNotEmpty)
            AppText(review.comment, style: AppTextStyles.regular14),
          if (date != null)
            AppText(
              DateFormat.yMMMd(
                context.locale.languageCode,
              ).format(date.toLocal()),
              style: AppTextStyles.regular12,
            ),
        ],
      ),
    );
  }
}
