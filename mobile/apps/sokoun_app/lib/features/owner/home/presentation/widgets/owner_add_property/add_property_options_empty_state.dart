import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class AddPropertyOptionsEmptyState extends StatelessWidget {
  const AddPropertyOptionsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Column(
    children: [
      ExcludeSemantics(
        child: Assets.lottie.noData.lottie(
          width: 104.r,
          height: 82.r,
          animate: !MediaQuery.disableAnimationsOf(context),
          repeat: false,
          package: 'melos_core',
        ),
      ),
      AppText(
        LocaleKeys.ownerAddPropertyOptionsEmptyTitle,
        style: AppTextStyles.bold14,
        textAlign: TextAlign.center,
      ),
    ],
  );
}
