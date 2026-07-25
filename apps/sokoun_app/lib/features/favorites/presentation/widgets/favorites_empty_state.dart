import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FavoritesEmptyState extends StatelessWidget {
  const FavoritesEmptyState({super.key, required this.onBrowseTap});

  final VoidCallback onBrowseTap;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(
          horizontal: AppPadding.pW20,
          vertical: AppPadding.pH20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 82.r,
              height: 82.r,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.tealAlpha07,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.favorite_border_rounded,
                color: AppColors.sokoonTeal,
                size: 36.r,
              ),
            ),
            AppSize.sH16.szH,
            AppText(
              LocaleKeys.favoritesEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: FontSize.s18,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            AppSize.sH8.szH,
            AppText(
              LocaleKeys.favoritesEmptyDescription,
              color: AppColors.sokoonGray,
              fontSize: FontSize.s13,
              fontWeight: FontWeight.w500,
              height: 1.45,
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            AppSize.sH20.szH,
            GestureDetector(
              onTap: onBrowseTap,
              behavior: HitTestBehavior.opaque,
              child: Container(
                height: AppSize.sH45,
                padding: EdgeInsets.symmetric(horizontal: AppPadding.pW20),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.sokoonTeal,
                  borderRadius: BorderRadius.circular(AppCircular.r12),
                ),
                child: AppText(
                  LocaleKeys.favoritesBrowseProperties,
                  color: AppColors.white,
                  fontSize: FontSize.s14,
                  fontWeight: FontWeight.w800,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
