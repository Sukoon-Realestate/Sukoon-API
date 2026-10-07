import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class RentalHomeEmptyState extends StatelessWidget {
  const RentalHomeEmptyState({super.key});

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      ExcludeSemantics(
        child: Assets.lottie.emptyBox.lottie(
          width: 96.r,
          height: 80.r,
          animate: !MediaQuery.of(context).disableAnimations,
          repeat: false,
          package: 'melos_core',
        ),
      ),
      AppText(
        LocaleKeys.rentalHomeEmpty,
        style: AppTextStyles.bold16.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
        ),
        textAlign: TextAlign.center,
      ),
      6.szH,
      AppText(
        LocaleKeys.rentalHomeEmptyHelp,
        style: AppTextStyles.regular14.copyWith(
          color: context.appColor(AppColors.sokoonGray),
        ),
        textAlign: TextAlign.center,
      ),
    ],
  ).paddingSymmetric(horizontal: 16, vertical: 12);
}
