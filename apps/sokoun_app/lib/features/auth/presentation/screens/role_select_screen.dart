import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_enum.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/select_role.dart';
import 'package:sokoun_app/features/auth/presentation/screens/welcome_screen.dart';

import '../widgets/role_select/role_option_card.dart';

class RoleSelectScreen extends StatelessWidget {
  const RoleSelectScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => SelectRoleCubit(),
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: 24.w),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        44.szH,
                        Align(
                          alignment: AlignmentDirectional.centerStart,
                          child: Container(
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
                          ),
                        ),
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
                        RoleOptionCard(
                          icon: Icons.home_work_outlined,
                          iconBackgroundColor: AppColors.mintLight,
                          iconColor: AppColors.sokoonTeal,
                          title: LocaleKeys.tenantRole,
                          subtitle: LocaleKeys.tenantRoleDescription,
                          isSelected: context.watch<SelectRoleCubit>().currentRole == UserType.tenant,
                          onTap: () => context.read<SelectRoleCubit>().selectRole(UserType.tenant),
                        ),
                        16.szH,
                        RoleOptionCard(
                          icon: Icons.key_rounded,
                          iconBackgroundColor: AppColors.goldPale,
                          iconColor: AppColors.sokoonGold,
                          title: LocaleKeys.propertyOwnerRole,
                          subtitle: LocaleKeys.propertyOwnerRoleDescription,
                          isSelected: context.watch<SelectRoleCubit>().currentRole == UserType.owner,
                          onTap: () => context.read<SelectRoleCubit>().selectRole(UserType.owner),
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
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
