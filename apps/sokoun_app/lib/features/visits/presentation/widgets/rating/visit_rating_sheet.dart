part of '../../../imports.dart';

class VisitRatingSheet extends StatefulWidget {
  const VisitRatingSheet({
    super.key,
    required this.propertyTitle,
    required this.onSubmitted,
  });

  final String propertyTitle;
  final void Function(int rating, String comment) onSubmitted;

  @override
  State<VisitRatingSheet> createState() => _VisitRatingSheetState();
}

class _VisitRatingSheetState extends State<VisitRatingSheet> {
  late final TextEditingController _commentController;
  late List<int> _criteriaRatings;
  int _overallRating = 0;

  List<String> get _criteria => [
    LocaleKeys.tenantVisitRatingCleanliness,
    LocaleKeys.tenantVisitRatingAccuracy,
    LocaleKeys.tenantVisitRatingOwnerTreatment,
  ];

  @override
  void initState() {
    super.initState();
    _commentController = TextEditingController();
    _criteriaRatings = [4, 4, 4];
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  void _updateCriterion(int index, int rating) {
    setState(() {
      _criteriaRatings[index] = rating;
    });
  }

  void _submit() {
    widget.onSubmitted(_overallRating, _commentController.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Container(
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
              Center(
                child: Container(
                  width: 48.w,
                  height: 5.h,
                  decoration: BoxDecoration(
                    color: AppColors.sokoonBorder,
                    borderRadius: BorderRadius.circular(999.r),
                  ),
                ),
              ),
              16.szH,
              Center(
                child: Container(
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
                ),
              ),
              12.szH,
              AppText(
                LocaleKeys.tenantVisitRateTitle,
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                fontWeight: FontWeight.w900,
                textAlign: TextAlign.center,
                maxLines: 2,
              ),
              4.szH,
              AppText(
                widget.propertyTitle,
                color: AppColors.sokoonGray,
                fontSize: 14.sp,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              14.szH,
              VisitRatingStars(
                rating: _overallRating,
                keyPrefix: 'visit-rating-overall',
                onRatingSelected: (rating) {
                  setState(() => _overallRating = rating);
                },
              ),
              12.szH,
              for (int index = 0; index < _criteria.length; index++) ...[
                _VisitRatingCriterion(
                  label: _criteria[index],
                  rating: _criteriaRatings[index],
                  keyPrefix: 'visit-rating-criterion-$index',
                  onRatingSelected: (rating) => _updateCriterion(index, rating),
                ),
                if (index < _criteria.length - 1) 8.szH,
              ],
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
                  key: const ValueKey('visit-rating-comment'),
                  controller: _commentController,
                  maxLines: 3,
                  style: TextStyle(
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    fontFamily: ConstantManager.fontFamily,
                  ),
                  decoration: InputDecoration(
                    hintText: LocaleKeys.tenantVisitRatingCommentHint,
                    hintStyle: TextStyle(
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                      fontFamily: ConstantManager.fontFamily,
                    ),
                    border: InputBorder.none,
                  ),
                ),
              ),
              14.szH,
              DefaultButton(
                key: const ValueKey('visit-rating-submit'),
                onTap: _submit,
                title: LocaleKeys.tenantVisitRatingSubmit,
                color: AppColors.sokoonTeal,
                textColor: AppColors.white,
                borderRadius: BorderRadius.circular(14.r),
                height: 50.h,
                fontSize: 15.sp,
                fontWeight: FontWeight.w900,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VisitRatingCriterion extends StatelessWidget {
  const _VisitRatingCriterion({
    required this.label,
    required this.rating,
    required this.keyPrefix,
    required this.onRatingSelected,
  });

  final String label;
  final int rating;
  final String keyPrefix;
  final ValueChanged<int> onRatingSelected;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: AppText(
            label,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
            maxLines: 1,
          ),
        ),
        VisitRatingStars(
          rating: rating,
          size: 18,
          keyPrefix: keyPrefix,
          onRatingSelected: onRatingSelected,
        ),
      ],
    );
  }
}
