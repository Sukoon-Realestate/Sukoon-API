import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

class FavoritesEmptyState extends StatelessWidget {
  const FavoritesEmptyState({
    super.key,
    this.isFiltered = false,
    this.onClearFiltersTap,
  });

  final bool isFiltered;
  final VoidCallback? onClearFiltersTap;

  void _handleAction() {
    if (isFiltered && onClearFiltersTap != null) {
      onClearFiltersTap!();
      return;
    }

    Go.to(const TenantSearchScreen());
  }

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(
        horizontal: AppPadding.pW20,
        vertical: AppPadding.pH20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.emptyBox.lottie(
              width: 136.r,
              height: 112.r,
              animate: !reduceMotion,
              repeat: false,
              fit: BoxFit.contain,
              package: 'melos_core',
            ),
          ),
          AppSize.sH8.szH,
          AppText(
            isFiltered
                ? LocaleKeys.tenantSearchResultsEmptyTitle
                : LocaleKeys.favoritesEmptyTitle,
            color: AppColors.sokoonNavy,
            fontSize: FontSize.s18,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
          ),
          AppSize.sH8.szH,
          AppText(
            isFiltered
                ? LocaleKeys.tenantSearchResultsEmptyDescription
                : LocaleKeys.favoritesEmptyDescription,
            color: AppColors.sokoonGray,
            fontSize: FontSize.s13,
            fontWeight: FontWeight.w500,
            height: 1.45,
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          AppSize.sH20.szH,
          DefaultButton(
            onTap: _handleAction,
            title: isFiltered
                ? LocaleKeys.tenantSearchResultsResetSearch
                : LocaleKeys.favoritesBrowseProperties,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(AppCircular.r12),
            height: AppSize.sH45,
            width: double.infinity,
            fontSize: FontSize.s14,
            fontWeight: FontWeight.w800,
          ),
        ],
      ),
    ).centerWidget;
  }
}
