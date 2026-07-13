import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

class RegisterHeader extends StatelessWidget {
  const RegisterHeader({super.key});

  @override
  Widget build(BuildContext context) {
    final isTenant = UserTypeHelper.instance.currentUserType.isTenant;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: AlignmentDirectional.centerEnd,
          child: SokoonBackButton(),
        ),
        14.szH,
        AppText(
          isTenant?
          LocaleKeys.createAccount :
          LocaleKeys.newOwnerSigningUp,
          color: AppColors.sokoonNavy,
          fontSize: 24.sp,
          fontWeight: FontWeight.w900,
        ),
        6.szH,
        AppText(
          isTenant?
          LocaleKeys.registerJourneySubtitle :
          LocaleKeys.createYourAccountToStartListingYourProperties,
          color: AppColors.sokoonGray,
          fontSize: 14.sp,
          fontWeight: FontWeight.w500,
        ),
      ],
    );
  }
}
