import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';

import 'home_avatar.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/workspace_switcher.dart';

class TenantHomeAppBarTitle extends StatelessWidget {
  const TenantHomeAppBarTitle({super.key});

  @override
  Widget build(BuildContext context) => StreamBuilder<UserState>(
    stream: injector.isRegistered<UserCubit>()
        ? UserCubit.instance.stream
        : null,
    builder: (context, snapshot) =>
        _buildHeader(snapshot.data?.userModel ?? UserModel.currentUser),
  );

  Widget _buildHeader(UserModel? user) {
    final String userName = user?.name.trim() ?? '';
    final String greeting = [
      LocaleKeys.welcome,
      if (userName.isNotEmpty) userName,
      '👋',
    ].join(' ');

    return Row(
      children: [
        const HomeAvatar(
          icon: Icons.person_outline_rounded,
          backgroundColor: AppColors.mintLight,
          iconColor: AppColors.sokoonTeal,
        ),
        10.szW,
        Expanded(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                greeting,
                style: AppTextStyles.bold.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 18.sp,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const WorkspaceSwitcher(workspace: AppWorkspace.tenant),
            ],
          ),
        ),
        10.szW,
        const NotificationBellButton(role: NotificationRole.tenant),
      ],
    );
  }
}
