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

/// ADD-LOC-PERM. The caller owns the native permission request and its result.
class LocationPermissionView extends StatelessWidget {
  const LocationPermissionView({
    super.key,
    required this.onAllowPressed,
    required this.onNotNowPressed,
  });

  final VoidCallback onAllowPressed;
  final VoidCallback onNotNowPressed;

  /// Returns true to request location access, false for "not now", or null
  /// when dismissed. This choice does not indicate an OS permission grant.
  static Future<bool?> show({BuildContext? context}) {
    return PermissionSheet.show(
      context: context,
      child: LocationPermissionView(
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
            icon: Icons.location_on_outlined,
            color: AppColors.sokoonTeal,
            backgroundColor: AppColors.tealAlpha06,
            title: LocaleKeys.locationPermissionTitle,
            description: LocaleKeys.locationPermissionDescription,
          ),
          20.szH,
          PermissionBenefits(
            backgroundColor: AppColors.tealAlpha03,
            children: [
              PermissionBenefitRow(
                title: LocaleKeys.locationPermissionNearbyTitle,
                description: LocaleKeys.locationPermissionNearbyDescription,
                color: AppColors.sokoonTeal,
              ),
              PermissionBenefitRow(
                title: LocaleKeys.locationPermissionMapTitle,
                description: LocaleKeys.locationPermissionMapDescription,
                color: AppColors.sokoonTeal,
              ),
            ],
          ),
          20.szH,
          PermissionActions(
            allowLabel: LocaleKeys.locationPermissionAllow,
            color: AppColors.sokoonTeal,
            shadowColor: AppColors.tealAlpha19,
            onAllowPressed: onAllowPressed,
            onNotNowPressed: onNotNowPressed,
          ),
        ],
      ),
    );
  }
}
