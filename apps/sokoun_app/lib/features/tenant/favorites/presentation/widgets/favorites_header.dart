import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/property_filter_button.dart';

class FavoritesHeader extends StatelessWidget {
  const FavoritesHeader({
    super.key,
    required this.itemCount,
    required this.activeFilterCount,
    required this.onFiltersPressed,
  });

  final int itemCount;
  final int activeFilterCount;
  final VoidCallback onFiltersPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
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
                fontWeight: FontWeight.w700,
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
        PropertyFilterButton(
          activeCount: activeFilterCount,
          onPressed: onFiltersPressed,
        ),
      ],
    ).padding(
      EdgeInsets.fromLTRB(
        AppPadding.pW20,
        AppPadding.pH4,
        AppPadding.pW20,
        AppPadding.pH12,
      ),
    );
  }
}
