import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class PropertyFilterButton extends StatelessWidget {
  const PropertyFilterButton({
    super.key,
    required this.onPressed,
    this.activeCount = 0,
  });

  final VoidCallback onPressed;
  final int activeCount;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: LocaleKeys.filter,
      child: Material(
        color: context.appColor(AppColors.white, surface: true),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.r),
          side: BorderSide(
            color: activeCount > 0
                ? context.appColor(AppColors.sokoonTeal)
                : context.appColor(AppColors.sokoonBorder),
          ),
        ),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(12.r),
          child: SizedBox.square(
            dimension: 44.r,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Center(
                  child: Icon(
                    Icons.tune_rounded,
                    color: context.appColor(AppColors.sokoonTeal),
                    size: 21.r,
                  ),
                ),
                if (activeCount > 0)
                  PositionedDirectional(
                    top: 3.h,
                    end: 3.w,
                    child: Container(
                      constraints: BoxConstraints(minWidth: 17.r),
                      height: 17.r,
                      padding: EdgeInsets.symmetric(horizontal: 4.w),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: context.appColor(
                          AppColors.sokoonTeal,
                          surface: true,
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: AppText(
                        '$activeCount',
                        style: AppTextStyles.black.copyWith(
                          color: AppColors.white,
                          fontSize: 9.sp,
                        ),
                        maxLines: 1,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
