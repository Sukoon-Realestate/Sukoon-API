import 'package:easy_localization/easy_localization.dart' hide TextDirection;
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../screens/property_reviews_screen.dart';

class PropertyRatingCard extends StatelessWidget {
  const PropertyRatingCard({
    super.key,
    required this.propertyId,
    required this.averageRating,
    required this.totalReviews,
  });

  final String propertyId;
  final double? averageRating;
  final int? totalReviews;

  @override
  Widget build(BuildContext context) {
    final String locale = context.locale.languageCode;
    final double? rating = averageRating;
    final int? count = totalReviews;
    final bool hasRating = count != null && count > 0 && rating != null;
    final String? reviewCount = count == null
        ? null
        : LocaleKeys.propertyReviewsCountLabel.replaceAll(
            '{count}',
            NumberFormat.decimalPattern(locale).format(count),
          );

    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            spacing: 12.w,
            children: [
              ExcludeSemantics(
                child: Container(
                  padding: EdgeInsets.all(10.r),
                  decoration: BoxDecoration(
                    color: context.appColor(AppColors.goldPale, surface: true),
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                  child: Icon(
                    Icons.rate_review_outlined,
                    color: AppColors.sokoonGold,
                    size: 22.r,
                  ),
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppText(
                      LocaleKeys.propertyReviewsTitle,
                      style: AppTextStyles.bold16.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                        fontSize: 16.sp,
                        height: 1.45,
                      ),
                    ),
                    2.szH,
                    AppText(
                      LocaleKeys.propertyReviewsVisitHint,
                      style: AppTextStyles.regular12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (count != null) 16.szH,
          if (hasRating)
            _PropertyRatingScore(rating: rating, reviewCount: reviewCount!)
          else if (count == 0) ...[
            AppText(
              LocaleKeys.propertyReviewsEmptyTitle,
              style: AppTextStyles.medium.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 14.sp,
                height: 1.45,
              ),
            ),
            4.szH,
            AppText(
              LocaleKeys.propertyReviewsEmptyDescription,
              style: AppTextStyles.regular13.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          ] else if (reviewCount != null)
            AppText(
              reviewCount,
              style: AppTextStyles.regular13.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          12.szH,
          Divider(height: 1, color: context.appColor(AppColors.sokoonBorder)),
          4.szH,
          TextButton(
            onPressed: propertyId.isEmpty
                ? null
                : () => Go.to(PropertyReviewsScreen(propertyId: propertyId)),
            style: TextButton.styleFrom(
              foregroundColor: context.appColor(AppColors.sokoonTeal),
              minimumSize: Size(48.w, 48.h),
              padding: EdgeInsets.symmetric(vertical: 12.h),
              alignment: AlignmentDirectional.centerStart,
            ),
            child: Row(
              spacing: 8.w,
              children: [
                Expanded(
                  child: AppText(
                    LocaleKeys.propertyReviewsViewAction,
                    style: AppTextStyles.bold14.copyWith(
                      color: context.appColor(AppColors.sokoonTeal),
                      fontSize: 14.sp,
                      height: 1.45,
                    ),
                  ),
                ),
                Icon(
                  Directionality.of(context) == TextDirection.rtl
                      ? Icons.chevron_left_rounded
                      : Icons.chevron_right_rounded,
                  size: 22.r,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PropertyRatingScore extends StatelessWidget {
  const _PropertyRatingScore({required this.rating, required this.reviewCount});

  final double rating;
  final String reviewCount;

  @override
  Widget build(BuildContext context) {
    final String score = NumberFormat(
      '0.0',
      context.locale.languageCode,
    ).format(rating);
    final Widget value = Semantics(
      label: LocaleKeys.propertyReviewsScoreLabel.replaceAll('{rating}', score),
      excludeSemantics: true,
      child: Directionality(
        textDirection: TextDirection.ltr,
        child: Wrap(
          crossAxisAlignment: WrapCrossAlignment.end,
          spacing: 6.w,
          runSpacing: 4.h,
          children: [
            AppText(
              score,
              style: AppTextStyles.extraBold.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 38.sp,
                height: 1.1,
              ),
            ),
            AppText(
              '/ ${NumberFormat.decimalPattern(context.locale.languageCode).format(5)}',
              style: AppTextStyles.regular14.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 14.sp,
              ),
            ),
          ],
        ),
      ),
    );
    final Widget details = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExcludeSemantics(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (int index = 0; index < 5; index++)
                Icon(
                  rating >= index + 1
                      ? Icons.star_rounded
                      : rating > index
                      ? Icons.star_half_rounded
                      : Icons.star_border_rounded,
                  color: AppColors.sokoonGold,
                  size: 22.r,
                ),
            ],
          ),
        ),
        6.szH,
        AppText(
          reviewCount,
          style: AppTextStyles.regular13.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
      ],
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        final bool stacked =
            constraints.maxWidth <
            MediaQuery.textScalerOf(context).scale(320.w);
        return stacked
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 12.h,
                children: [value, details],
              )
            : Row(
                spacing: 20.w,
                children: [
                  value,
                  Expanded(child: details),
                ],
              );
      },
    );
  }
}
