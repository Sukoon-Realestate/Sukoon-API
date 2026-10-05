part of '../../../imports.dart';

class OwnerReviewsCard extends StatelessWidget {
  const OwnerReviewsCard({super.key, required this.reviews});

  final List<OwnerProfileReviewContent> reviews;

  @override
  Widget build(BuildContext context) {
    return ProfileSurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.profileLatestReviews,
            style: AppTextStyles.bold14.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          4.szH,
          if (reviews.isEmpty) const OwnerReviewsEmptyState(),
          ...reviews.indexed.map((entry) {
            final int index = entry.$1;
            final OwnerProfileReviewContent review = entry.$2;
            return Container(
              padding: EdgeInsets.symmetric(vertical: 10.h),
              decoration: BoxDecoration(
                border: index < reviews.length - 1
                    ? Border(
                        bottom: BorderSide(
                          color: context.appColor(AppColors.sokoonBorder),
                        ),
                      )
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 4.h,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: AppText(
                          review.reviewerName.isNotEmpty
                              ? review.reviewerName
                              : LocaleKeys.profileFallbackName,
                          style: AppTextStyles.bold12.copyWith(
                            color: context.appColor(AppColors.sokoonNavy),
                            fontSize: 12.sp,
                            height: 1.45,
                          ),
                        ),
                      ),
                      Row(
                        children: List.generate(
                          5,
                          (starIndex) => Icon(
                            Icons.star_rounded,
                            color: starIndex < review.rating.round()
                                ? context.appColor(AppColors.amber)
                                : context.appColor(AppColors.graySoft),
                            size: 13.r,
                          ),
                        ),
                      ),
                    ],
                  ),
                  AppText(
                    review.comment,
                    style: AppTextStyles.regular12.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: 12.sp,
                      height: 1.45,
                    ),
                  ),
                  if (review.dateLabel.isNotEmpty)
                    AppText(
                      review.dateLabel,
                      style: AppTextStyles.regular10.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 10.sp,
                        height: 1.45,
                      ),
                    ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
