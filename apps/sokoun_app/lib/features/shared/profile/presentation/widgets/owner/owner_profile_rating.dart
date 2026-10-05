part of '../../../imports.dart';

class OwnerProfileRating extends StatelessWidget {
  const OwnerProfileRating({
    super.key,
    required this.rating,
    required this.reviewsCount,
    required this.label,
  });

  final double rating;
  final int reviewsCount;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
    spacing: 4.w,
    children: [
      Icon(
        Icons.star_rounded,
        color: context.appColor(AppColors.amber),
        size: 14.r,
      ),
      Flexible(
        child: AppText(
          label.isNotEmpty
              ? label
              : LocaleKeys.profileRatingSummaryLabel
                    .replaceAll('{rating}', rating.toStringAsFixed(1))
                    .replaceAll('{count}', '$reviewsCount'),
          style: AppTextStyles.regular12.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            height: 1.45,
          ),
        ),
      ),
    ],
  );
}
