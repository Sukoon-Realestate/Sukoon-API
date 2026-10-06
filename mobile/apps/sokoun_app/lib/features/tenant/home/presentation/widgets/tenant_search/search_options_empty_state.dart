import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class SearchPropertyTypesEmptyState extends StatelessWidget {
  const SearchPropertyTypesEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    return _SearchOptionsEmptyState(
      title: LocaleKeys.tenantSearchPropertyTypesEmptyTitle,
      description: LocaleKeys.tenantSearchPropertyTypesEmptyDescription,
      animation: Assets.lottie.emptyBox,
    );
  }
}

class SearchAvailablePlacesEmptyState extends StatelessWidget {
  const SearchAvailablePlacesEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    return _SearchOptionsEmptyState(
      title: LocaleKeys.tenantSearchNoAvailablePlaces,
      description: LocaleKeys.tenantSearchAvailablePlacesEmptyDescription,
      animation: Assets.lottie.notFound1,
    );
  }
}

class _SearchOptionsEmptyState extends StatelessWidget {
  const _SearchOptionsEmptyState({
    required this.title,
    required this.description,
    required this.animation,
  });

  final String title;
  final String description;
  final LottieGenImage animation;

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: title,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        spacing: 4.h,
        children: [
          ExcludeSemantics(
            child: animation.lottie(
              width: 104.r,
              height: 82.r,
              animate: !reduceMotion,
              repeat: false,
              fit: BoxFit.contain,
              package: 'melos_core',
            ),
          ),
          AppText(
            title,
            style: AppTextStyles.bold14.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          AppText(
            description,
            style: AppTextStyles.medium12.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 12.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
        ],
      ).paddingSymmetric(vertical: 8.h),
    );
  }
}
