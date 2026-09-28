import 'package:flutter/material.dart';

import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../extensions/sized_box_helper.dart';
import '../navigation/navigator.dart';
import 'permissions/permission_actions.dart';
import 'permissions/permission_benefit_row.dart';
import 'permissions/permission_benefits.dart';
import 'permissions/permission_header.dart';
import 'permissions/permission_sheet.dart';

class NotificationPermissionView extends StatelessWidget {
  const NotificationPermissionView({
    super.key,
    required this.onAllowPressed,
    required this.onNotNowPressed,
  });

  final VoidCallback onAllowPressed;
  final VoidCallback onNotNowPressed;

  static Future<bool?> show({BuildContext? context}) {
    return PermissionSheet.show(
      context: context,
      child: NotificationPermissionView(
        onAllowPressed: () => Go.back(true),
        onNotNowPressed: () => Go.back(false),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PermissionSheet(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          PermissionHeader(
            icon: Icons.notifications_none_rounded,
            color: AppColors.blue,
            backgroundColor: AppColors.blueAlpha06,
            title: LocaleKeys.notificationPermissionTitle,
            description: LocaleKeys.notificationPermissionDescription,
          ),
          18.szH,
          PermissionBenefits(
            backgroundColor: AppColors.grayOffWhite,
            children: [
              PermissionBenefitRow(
                title: LocaleKeys.notificationPermissionVisitsTitle,
                description: LocaleKeys.notificationPermissionVisitsDescription,
                color: AppColors.sokoonTeal,
                backgroundColor: AppColors.tealAlpha08,
              ),
              PermissionBenefitRow(
                title: LocaleKeys.notificationPermissionMessagesTitle,
                description:
                    LocaleKeys.notificationPermissionMessagesDescription,
                color: AppColors.sokoonGold,
                backgroundColor: AppColors.goldAlpha08,
              ),
              PermissionBenefitRow(
                title: LocaleKeys.notificationPermissionPropertiesTitle,
                description:
                    LocaleKeys.notificationPermissionPropertiesDescription,
                color: AppColors.green,
                backgroundColor: AppColors.greenAlpha08,
              ),
            ],
          ),
          20.szH,
          PermissionActions(
            allowLabel: LocaleKeys.notificationPermissionTitle,
            color: AppColors.blue,
            shadowColor: AppColors.blueAlpha19,
            onAllowPressed: onAllowPressed,
            onNotNowPressed: onNotNowPressed,
          ),
        ],
      ),
    );
  }
}
