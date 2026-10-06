part of '../../../imports.dart';

class LanguageOptionCard extends StatelessWidget {
  const LanguageOptionCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.flag,
    required this.selected,
    required this.onSelected,
  });

  final String title;
  final String subtitle;
  final String flag;
  final bool selected;
  final VoidCallback onSelected;

  @override
  Widget build(BuildContext context) {
    final BorderRadius borderRadius = BorderRadius.circular(14.r);
    final Color borderColor = selected
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonBorder);

    return Semantics(
      checked: selected,
      inMutuallyExclusiveGroup: true,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: borderRadius,
          boxShadow: selected
              ? [
                  BoxShadow(
                    color: AppColors.tealAlpha08,
                    blurRadius: 16.r,
                    offset: Offset(0, 4.h),
                  ),
                ]
              : const [],
        ),
        child: Material(
          color: context.appColor(AppColors.white, surface: true),
          shape: RoundedRectangleBorder(
            borderRadius: borderRadius,
            side: BorderSide(color: context.appColor(borderColor), width: 2.r),
          ),
          child: InkWell(
            onTap: onSelected,
            borderRadius: borderRadius,
            child: Row(
              spacing: 14.w,
              children: [
                Container(
                  width: 22.r,
                  height: 22.r,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: context.appColor(borderColor),
                      width: 2.r,
                    ),
                  ),
                  child: selected
                      ? Container(
                          width: 12.r,
                          height: 12.r,
                          decoration: BoxDecoration(
                            color: context.appColor(
                              AppColors.sokoonTeal,
                              surface: true,
                            ),
                            shape: BoxShape.circle,
                          ),
                        )
                      : null,
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AppText(
                        title,
                        style: AppTextStyles.extraBold.copyWith(
                          color: context.appColor(AppColors.sokoonNavy),
                          fontSize: 16.sp,
                          height: 1.5,
                        ),
                      ),
                      AppText(
                        subtitle,
                        style: AppTextStyles.medium12.copyWith(
                          color: context.appColor(AppColors.sokoonGray),
                          fontSize: 12.sp,
                          height: 1.5,
                        ),
                      ).showIf(condition: () => subtitle != title),
                    ],
                  ),
                ),
                ExcludeSemantics(
                  child: AppText(
                    flag,
                    style: AppTextStyles.regular.copyWith(
                      fontSize: 28.sp,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ).paddingSymmetric(horizontal: 18.w, vertical: 16.h),
          ),
        ),
      ),
    );
  }
}
