import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';

class SponsoredListingBadge extends StatelessWidget {
  const SponsoredListingBadge({super.key});
  @override
  Widget build(BuildContext context) => AppText(
    LocaleKeys.paidSponsored,
    fontSize: 12,
    fontWeight: FontWeight.w600,
    color: context.appColor(AppColors.sokoonNavy),
  ).paddingOnly(bottom: 8);
}
