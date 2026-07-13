import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class LoginHeader extends StatelessWidget {
  const LoginHeader({super.key});

  @override
  Widget build(BuildContext context) {
    final isTenant = UserTypeHelper.instance.currentUserType.isTenant;

    return Column(
      children: [
        Container(
          width: 60.r,
          height: 60.r,
          decoration: BoxDecoration(
            color: AppColors.sokoonTeal,
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Icon(
            Icons.favorite_rounded,
            color: AppColors.white,
            size: 28.r,
          ),
        ),
        12.szH,
        AppText(
          isTenant ? LocaleKeys.login : LocaleKeys.signInAsOwner,
          color: AppColors.sokoonNavy,
          fontSize: 22.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
        ),
        4.szH,
        AppText(
          LocaleKeys.welcomeBackToSokoon,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w500,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
