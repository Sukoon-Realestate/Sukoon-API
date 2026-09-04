part of '../../../imports.dart';

class OwnerReviewsCard extends StatelessWidget {
  const OwnerReviewsCard({super.key});

  @override
  Widget build(BuildContext context) {
    final List<({String name, String text, int rating})> reviews = [
      (
        name: LocaleKeys.profileReviewSaraName,
        text: LocaleKeys.profileReviewSaraText,
        rating: 5,
      ),
      (
        name: LocaleKeys.profileReviewMohamedName,
        text: LocaleKeys.profileReviewMohamedText,
        rating: 4,
      ),
    ];

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
          ...reviews.indexed.map((entry) {
            final int index = entry.$1;
            final ({String name, String text, int rating}) review = entry.$2;
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
                          review.name,
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
                            color: starIndex < review.rating
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
                    review.text,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
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
