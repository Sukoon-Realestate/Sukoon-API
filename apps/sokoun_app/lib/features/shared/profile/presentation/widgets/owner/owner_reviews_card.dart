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
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
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
                    ? const Border(
                        bottom: BorderSide(color: AppColors.sokoonBorder),
                      )
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: AppText(
                          review.reviewerName.isNotEmpty
                              ? review.reviewerName
                              : LocaleKeys.profileFallbackName,
                          color: AppColors.sokoonNavy,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Row(
                        children: List.generate(
                          5,
                          (starIndex) => Icon(
                            Icons.star_rounded,
                            color: starIndex < review.rating.round()
                                ? AppColors.amber
                                : AppColors.graySoft,
                            size: 13.r,
                          ),
                        ),
                      ),
                    ],
                  ),
                  4.szH,
                  AppText(
                    review.comment,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                  ),
                  if (review.dateLabel.isNotEmpty) ...[
                    4.szH,
                    AppText(
                      review.dateLabel,
                      color: AppColors.sokoonGray,
                      fontSize: 10.sp,
                    ),
                  ],
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
