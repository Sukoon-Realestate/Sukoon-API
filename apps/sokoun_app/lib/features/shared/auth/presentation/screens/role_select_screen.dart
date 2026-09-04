import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/role_select/role_option_card.dart';

class RoleSelectScreen extends StatelessWidget {
  RoleSelectScreen({super.key});

  final ValueNotifier<UserType> _currentUserType = ValueNotifier(
    UserTypeHelper.instance.currentUserType,
  );
  void _selectNewType(UserType type) {
    UserTypeHelper.instance.setUserType(type);
    _currentUserType.value = type;
  }

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          44.szH,
          Container(
            width: 52.r,
            height: 52.r,
            decoration: BoxDecoration(
              color: AppColors.mintLight,
              borderRadius: BorderRadius.circular(16.r),
            ),
            child: Icon(
              Icons.home_outlined,
              color: AppColors.sokoonTeal,
              size: 24.r,
            ),
          ).startWidget,
          24.szH,
          AppText(
            LocaleKeys.youAre,
            color: AppColors.sokoonNavy,
            fontSize: 28.sp,
            fontWeight: FontWeight.w900,
          ),
          8.szH,
          AppText(
            LocaleKeys.chooseAccountTypeToContinue,
            color: AppColors.sokoonGray,
            fontSize: 15.sp,
            fontWeight: FontWeight.w400,
          ),
          36.szH,
          ValueListenableBuilder(
            valueListenable: _currentUserType,
            builder: (context, type, child) => Column(
              children: [
                RoleOptionCard(
                  icon: Icons.home_work_outlined,
                  iconBackgroundColor: AppColors.mintLight,
                  iconColor: AppColors.sokoonTeal,
                  title: LocaleKeys.tenantRole,
                  subtitle: LocaleKeys.tenantRoleDescription,
                  isSelected: type.isTenant,
                  onTap: () => _selectNewType(UserType.tenant),
                ),
                16.szH,
                RoleOptionCard(
                  icon: Icons.key_rounded,
                  iconBackgroundColor: AppColors.goldPale,
                  iconColor: AppColors.sokoonGold,
                  title: LocaleKeys.propertyOwnerRole,
                  subtitle: LocaleKeys.propertyOwnerRoleDescription,
                  isSelected: type.isOwner,
                  onTap: () => _selectNewType(UserType.owner),
                ),
              ],
            ),
          ),
          32.szH,
          DefaultButton(
            onTap: () => Go.to(const WelcomeScreen()),
            title: LocaleKeys.continueButton,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
          24.szH,
        ],
      ),
    );
  }
}
