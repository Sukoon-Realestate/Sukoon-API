import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:easy_localization/easy_localization.dart' hide TextDirection;
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import '../../data/models/my_review.dart';

class MyReviewCard extends StatelessWidget {
  const MyReviewCard({super.key, required this.review});
  final MyReview review;
  @override
  Widget build(BuildContext context) {
    final DateTime? createdAt = DateTime.tryParse(review.createdAt);
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 6.h),
      color: context.appColor(AppColors.white, surface: true),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.r),
        side: BorderSide(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16.r),
        onTap: review.propertyId.isEmpty
            ? null
            : () => Go.to(
                PropertyDetailsScreen(
                  propertyId: review.propertyId,
                  offerId: review.rentalSelection?.offerId,
                ),
              ),
        child: Padding(
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 12.w,
                children: [
                  if (review.propertyImage.isNotEmpty)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12.r),
                      child: Image.network(
                        review.propertyImage,
                        width: 64.r,
                        height: 64.r,
                        fit: BoxFit.cover,
                        excludeFromSemantics: true,
                        errorBuilder: (_, __, ___) =>
                            Icon(Icons.home_outlined, size: 48.r),
                      ),
                    ),
                  Expanded(
                    child: AppText(
                      review.propertyTitle,
                      style: AppTextStyles.bold16.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                      ),
                    ),
                  ),
                ],
              ),
              10.szH,
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
                      '${review.rating.toStringAsFixed(1)} / 5',
                      style: AppTextStyles.bold14,
                    ),
                  ),
                ],
              ),
              if (review.rentalSelection != null)
                AppText(
                  RentalOfferLabels.accommodation(review.rentalSelection!),
                ),
              if (review.comment.isNotEmpty) ...[
                8.szH,
                AppText(
                  review.comment,
                  style: AppTextStyles.regular14.copyWith(height: 1.5),
                ),
              ],
              if (createdAt != null) ...[
                8.szH,
                AppText(
                  DateFormat.yMMMd(
                    context.locale.languageCode,
                  ).format(createdAt.toLocal()),
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
