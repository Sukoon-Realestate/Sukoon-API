import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

class WelcomeScreenContent {
  const WelcomeScreenContent({
    required this.headerIcon,
    required this.headerIconBackgroundColor,
    required this.headerIconColor,
    required this.title,
    required this.description,
    required this.features,
    required this.primaryButtonTitle,
    required this.loginButtonTitle,
  });

  final IconData headerIcon;
  final Color headerIconBackgroundColor;
  final Color headerIconColor;
  final String title;
  final String description;
  final List<WelcomeFeatureContent> features;
  final String primaryButtonTitle;
  final String loginButtonTitle;

  factory WelcomeScreenContent.account() => WelcomeScreenContent(
    headerIcon: Icons.home_work_outlined,
    headerIconBackgroundColor: AppColors.mintLight,
    headerIconColor: AppColors.sokoonTeal,
    title: LocaleKeys.welcomeToSokoon,
    description: LocaleKeys.workspaceAccountDescription,
    features: [
      WelcomeFeatureContent(
        icon: Icons.search_rounded,
        iconBackgroundColor: AppColors.mintLight,
        iconColor: AppColors.sokoonTeal,
        title: LocaleKeys.searchEasily,
        subtitle: LocaleKeys.thousandsPropertiesAcrossEgypt,
      ),
      WelcomeFeatureContent(
        icon: Icons.home_work_outlined,
        iconBackgroundColor: AppColors.goldPale,
        iconColor: AppColors.sokoonGold,
        title: LocaleKeys.addPropertiesEasily,
        subtitle: LocaleKeys.fourSimpleStepsPropertyLive,
      ),
    ],
    primaryButtonTitle: LocaleKeys.createAccount,
    loginButtonTitle: LocaleKeys.haveAccountLogin,
  );
}

class WelcomeFeatureContent {
  const WelcomeFeatureContent({
    required this.icon,
    required this.iconBackgroundColor,
    required this.iconColor,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final Color iconBackgroundColor;
  final Color iconColor;
  final String title;
  final String subtitle;
}
