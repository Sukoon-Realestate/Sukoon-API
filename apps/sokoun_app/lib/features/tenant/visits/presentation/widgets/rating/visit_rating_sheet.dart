part of '../../../imports.dart';

class VisitRatingSheet extends StatefulWidget {
  const VisitRatingSheet({super.key, required this.propertyTitle});

  final String propertyTitle;

  @override
  State<VisitRatingSheet> createState() => _VisitRatingSheetState();
}

class _VisitRatingSheetState extends State<VisitRatingSheet> {
  late final TextEditingController _commentController;
  final ValueNotifier<List<int>> _criteriaRatings = ValueNotifier<List<int>>(
    <int>[4, 4, 4],
  );
  final ValueNotifier<int> _overallRating = ValueNotifier<int>(0);

  List<String> get _criteria => [
    LocaleKeys.tenantVisitRatingCleanliness,
    LocaleKeys.tenantVisitRatingAccuracy,
    LocaleKeys.tenantVisitRatingOwnerTreatment,
  ];

  @override
  void initState() {
    super.initState();
    _commentController = TextEditingController();
  }

  @override
  void dispose() {
    _commentController.dispose();
    _criteriaRatings.dispose();
    _overallRating.dispose();
    super.dispose();
  }

  void _updateCriterion(int index, int rating) {
    final List<int> ratings = List<int>.of(_criteriaRatings.value);
    ratings[index] = rating;
    _criteriaRatings.value = ratings;
  }

  void _submit() => Go.back(true);

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(maxHeight: 0.92.sh),
      padding: EdgeInsets.fromLTRB(
        24.w,
        10.h,
        24.w,
        MediaQuery.viewInsetsOf(context).bottom + 24.h,
      ),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 48.w,
              height: 5.h,
              decoration: BoxDecoration(
                color: AppColors.sokoonBorder,
                borderRadius: BorderRadius.circular(999.r),
              ),
            ).centerWidget,
            16.szH,
            Container(
              width: 56.r,
              height: 56.r,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.goldPale,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.star_rounded,
                color: AppColors.gold,
                size: 28.r,
              ),
            ).centerWidget,
            12.szH,
            AppText(
              LocaleKeys.tenantVisitRateTitle,
              style: AppTextStyles.bold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            4.szH,
            AppText(
              widget.propertyTitle,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 14.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            14.szH,
            ValueListenableBuilder<int>(
              valueListenable: _overallRating,
              builder: (context, overallRating, _) => VisitRatingStars(
                rating: overallRating,
                onRatingSelected: (rating) => _overallRating.value = rating,
              ),
            ),
            12.szH,
            ValueListenableBuilder<List<int>>(
              valueListenable: _criteriaRatings,
              builder: (context, criteriaRatings, _) => Column(
                spacing: 8.h,
                children: [
                  for (int index = 0; index < _criteria.length; index++)
                    _VisitRatingCriterion(
                      label: _criteria[index],
                      rating: criteriaRatings[index],
                      onRatingSelected: (rating) =>
                          _updateCriterion(index, rating),
                    ),
                ],
              ),
            ),
            16.szH,
            Container(
              height: 80.h,
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              decoration: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(16.r),
                border: Border.all(color: AppColors.sokoonBorder),
              ),
              child: TextField(
                controller: _commentController,
                maxLines: 3,
                style: AppTextStyles.base.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                ),
                decoration: InputDecoration(
                  hintText: LocaleKeys.tenantVisitRatingCommentHint,
                  hintStyle: AppTextStyles.base.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 13.sp,
                  ),
                  border: InputBorder.none,
                ),
              ),
            ),
            14.szH,
            DefaultButton(
              onTap: _submit,
              title: LocaleKeys.tenantVisitRatingSubmit,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(14.r),
              height: 50.h,
              textStyle: AppTextStyles.bold15.copyWith(
                fontSize: 15.sp,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VisitRatingCriterion extends StatelessWidget {
  const _VisitRatingCriterion({
    required this.label,
    required this.rating,
    required this.onRatingSelected,
  });

  final String label;
  final int rating;
  final ValueChanged<int> onRatingSelected;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: AppText(
            label,
            style: AppTextStyles.bold14.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              height: 1.45,
            ),
            maxLines: 1,
          ),
        ),
        VisitRatingStars(
          rating: rating,
          size: 18,
          onRatingSelected: onRatingSelected,
        ),
      ],
    );
  }
}
