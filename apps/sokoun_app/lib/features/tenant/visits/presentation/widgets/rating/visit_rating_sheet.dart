part of '../../../imports.dart';

class VisitRatingSheet extends StatefulWidget {
  const VisitRatingSheet({
    super.key,
    required this.propertyTitle,
    this.visitId = '',
  });

  final String propertyTitle;
  final String visitId;

  @override
  State<VisitRatingSheet> createState() => _VisitRatingSheetState();
}

class _VisitRatingSheetState extends State<VisitRatingSheet> {
  final List<GlobalKey> _ratingFieldKeys = List.generate(3, (_) => GlobalKey());
  late final TextEditingController _commentController;
  final ValueNotifier<List<int>> _criteriaRatings = ValueNotifier<List<int>>(
    <int>[0, 0, 0],
  );
  late final VisitReviewCubit _reviewCubit;

  List<String> get _criteria => [
    LocaleKeys.tenantVisitRatingCleanliness,
    LocaleKeys.tenantVisitRatingAccuracy,
    LocaleKeys.tenantVisitRatingOwnerTreatment,
  ];

  String? _validateRating(String? value) =>
      Validators.isValidRatings([int.tryParse(value ?? '') ?? 0])
      ? null
      : LocaleKeys.fillField;

  List<FirstValidationErrorField> _validationFields() => [
    for (int index = 0; index < _criteria.length; index++)
      FirstValidationErrorField(
        fieldKey: _ratingFieldKeys[index],
        title: _criteria[index],
        value: '${_criteriaRatings.value[index]}',
        validator: _validateRating,
      ),
  ];

  @override
  void initState() {
    super.initState();
    _commentController = TextEditingController();
    _reviewCubit = VisitReviewCubit();
  }

  @override
  void dispose() {
    _commentController.dispose();
    _criteriaRatings.dispose();
    _reviewCubit.close();
    super.dispose();
  }

  void _updateCriterion(int index, int rating) {
    final List<int> ratings = List<int>.of(_criteriaRatings.value);
    ratings[index] = rating;
    _criteriaRatings.value = ratings;
  }

  Future<void> _submit() async {
    final List<int> values = _criteriaRatings.value;
    final bool succeeded = await _reviewCubit.submit(
      visitId: widget.visitId,
      body: VisitReviewBody(
        cleanliness: values[0],
        accuracy: values[1],
        ownerInteraction: values[2],
        comment: _commentController.text,
      ),
    );
    if (succeeded && mounted) Go.back(true);
  }

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
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: FirstValidationErrorForm(
        validationFields: _validationFields,
        onValid: _submit,
        builder: (context, submit) => SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                width: 48.w,
                height: 5.h,
                decoration: BoxDecoration(
                  color: context.appColor(
                    AppColors.sokoonBorder,
                    surface: true,
                  ),
                  borderRadius: BorderRadius.circular(999.r),
                ),
              ).centerWidget,
              16.szH,
              Container(
                width: 56.r,
                height: 56.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: context.appColor(AppColors.goldPale, surface: true),
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
                  color: context.appColor(AppColors.sokoonNavy),
                  fontSize: 20.sp,
                ),
                textAlign: TextAlign.center,
                maxLines: 2,
              ),
              4.szH,
              AppText(
                widget.propertyTitle,
                style: AppTextStyles.regular14.copyWith(
                  color: context.appColor(AppColors.sokoonGray),
                  fontSize: 14.sp,
                  height: 1.45,
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              14.szH,
              ValueListenableBuilder<List<int>>(
                valueListenable: _criteriaRatings,
                builder: (context, criteriaRatings, _) => Column(
                  spacing: 8.h,
                  children: [
                    for (int index = 0; index < _criteria.length; index++)
                      SokounValidationField(
                        key: _ratingFieldKeys[index],
                        value: '${criteriaRatings[index]}',
                        validator: _validateRating,
                        child: _VisitRatingCriterion(
                          label: _criteria[index],
                          rating: criteriaRatings[index],
                          onRatingSelected: (rating) =>
                              _updateCriterion(index, rating),
                        ),
                      ),
                  ],
                ),
              ),
              16.szH,
              Container(
                height: 80.h,
                padding: EdgeInsets.symmetric(horizontal: 14.w),
                decoration: BoxDecoration(
                  color: context.appColor(AppColors.white, surface: true),
                  borderRadius: BorderRadius.circular(16.r),
                  border: Border.all(
                    color: context.appColor(AppColors.sokoonBorder),
                  ),
                ),
                child: DefaultTextField(
                  controller: _commentController,
                  inputType: TextInputType.multiline,
                  action: TextInputAction.newline,
                  maxLines: 3,
                  style: AppTextStyles.base.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 13.sp,
                  ),
                  decoration: InputDecoration(
                    hintText: LocaleKeys.tenantVisitRatingCommentHint,
                    hintStyle: AppTextStyles.base.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: 13.sp,
                    ),
                    border: InputBorder.none,
                  ),
                ),
              ),
              14.szH,
              ValueListenableBuilder<List<int>>(
                valueListenable: _criteriaRatings,
                builder: (context, ratings, _) =>
                    !Validators.isNonBlank(widget.visitId)
                    ? DefaultButton(
                        onTap: null,
                        title: LocaleKeys.tenantVisitRatingSubmit,
                      )
                    : AppLoadingButton(
                        asyncCall: (_) => submit(),
                        title: LocaleKeys.tenantVisitRatingSubmit,
                        buttonColor: context.appColor(
                          AppColors.sokoonTeal,
                          surface: true,
                        ),
                      ),
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
              color: context.appColor(AppColors.sokoonNavy),
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
