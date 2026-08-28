import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FavoritesHeader extends StatelessWidget {
  const FavoritesHeader({
    super.key,
    required this.itemCount,
    this.onSelectAllPressed,
  });

  final int itemCount;
  final VoidCallback? onSelectAllPressed;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        AppPadding.pW20,
        AppPadding.pH4,
        AppPadding.pW20,
        AppPadding.pH12,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  LocaleKeys.favoritesTitle,
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.start,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppSize.sH4.szH,
                AppText(
                  '$itemCount ${LocaleKeys.favoritesSavedPropertiesCount}',
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w400,
                  textAlign: TextAlign.start,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          AppSize.sW8.szW,
          TextButton(
            onPressed: onSelectAllPressed,
            style: TextButton.styleFrom(
              foregroundColor: AppColors.sokoonGray,
              disabledForegroundColor: AppColors.sokoonGray,
              minimumSize: Size.zero,
              padding: EdgeInsets.symmetric(
                horizontal: AppPadding.pW4,
                vertical: AppPadding.pH4,
              ),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              LocaleKeys.favoritesSelectAll,
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
