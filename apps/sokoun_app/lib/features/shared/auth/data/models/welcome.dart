import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';

class WelcomeScreenContent {
  const WelcomeScreenContent({
    required this.isOwner,
    required this.headerIcon,
    required this.headerIconBackgroundColor,
    required this.headerIconColor,
    required this.title,
    required this.description,
    required this.features,
    required this.primaryButtonTitle,
    required this.loginButtonTitle,
  });

  final bool isOwner;
  final IconData headerIcon;
  final Color headerIconBackgroundColor;
  final Color headerIconColor;
  final String title;
  final String description;
  final List<WelcomeFeatureContent> features;
  final String primaryButtonTitle;
  final String loginButtonTitle;

  factory WelcomeScreenContent.fromRole(UserType role) {
    if (role.isOwner) {
      return WelcomeScreenContent(
        isOwner: true,
        headerIcon: Icons.key_rounded,
        headerIconBackgroundColor: AppColors.goldPale,
        headerIconColor: AppColors.sokoonGold,
        title: LocaleKeys.ownerWelcomeTitle,
        description: LocaleKeys.ownerWelcomeDescription,
        features: <WelcomeFeatureContent>[
          WelcomeFeatureContent(
            icon: Icons.home_work_outlined,
            iconBackgroundColor: AppColors.goldPale,
            iconColor: AppColors.sokoonGold,
            title: LocaleKeys.addPropertiesEasily,
            subtitle: LocaleKeys.fourSimpleStepsPropertyLive,
          ),
          WelcomeFeatureContent(
            icon: Icons.verified_user_outlined,
            iconBackgroundColor: AppColors.mintLight,
            iconColor: AppColors.sokoonTeal,
            title: LocaleKeys.verifiedTenantsOnly,
            subtitle: LocaleKeys.allTenantsIdentityVerified,
          ),
          WelcomeFeatureContent(
            icon: Icons.bar_chart_rounded,
            iconBackgroundColor: AppColors.bluePale,
            iconColor: AppColors.blue,
            title: LocaleKeys.detailedStatistics,
            subtitle: LocaleKeys.trackViewsAndVisitRequests,
          ),
        ],
        primaryButtonTitle: LocaleKeys.startAsOwner,
        loginButtonTitle: LocaleKeys.haveOwnerAccountLogin,
      );
    }

    return WelcomeScreenContent(
      isOwner: false,
      headerIcon: Icons.shield_outlined,
      headerIconBackgroundColor: AppColors.mintLight,
      headerIconColor: AppColors.sokoonTeal,
      title: LocaleKeys.welcomeToSokoon,
      description: LocaleKeys.sokoonWelcomeDescription,
      features: <WelcomeFeatureContent>[
        WelcomeFeatureContent(
          icon: Icons.search_rounded,
          iconBackgroundColor: AppColors.mintLight,
          iconColor: AppColors.sokoonTeal,
          title: LocaleKeys.searchEasily,
          subtitle: LocaleKeys.thousandsPropertiesAcrossEgypt,
        ),
        WelcomeFeatureContent(
          icon: Icons.verified_user_outlined,
          iconBackgroundColor: AppColors.greenPale,
          iconColor: AppColors.green,
          title: LocaleKeys.safetyAndReliability,
          subtitle: LocaleKeys.verifiedOwnersReviewedProperties,
        ),
        WelcomeFeatureContent(
          icon: Icons.chat_bubble_outline_rounded,
          iconBackgroundColor: AppColors.bluePale,
          iconColor: AppColors.blue,
          title: LocaleKeys.directContact,
          subtitle: LocaleKeys.directChatWithOwnersAfterVerification,
        ),
      ],
      primaryButtonTitle: LocaleKeys.startHousingSearch,
      loginButtonTitle: LocaleKeys.haveAccountLogin,
    );
  }
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
