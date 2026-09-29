import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';

import 'home_avatar.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/workspace_switcher.dart';

class OwnerHeader extends StatelessWidget {
  const OwnerHeader({
    super.key,
    required this.avatarUrl,
    required this.isVerified,
  });

  final String? avatarUrl;
  final bool isVerified;

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
      LocaleKeys.ownerHomeGreetingPrefix,
      if (userName.isNotEmpty) userName,
      '👋',
    ].join(' ');

    return Row(
      children: [
        HomeAvatar(
          icon: Icons.key_rounded,
          backgroundColor: AppColors.goldPale,
          iconColor: AppColors.gold,
          imageUrl: avatarUrl,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                greeting,
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w700,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const WorkspaceSwitcher(workspace: AppWorkspace.owner),
              4.szH,
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: isVerified ? AppColors.goldPale : AppColors.grayPale,
                  borderRadius: BorderRadius.circular(999.r),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isVerified
                          ? Icons.verified_rounded
                          : Icons.info_outline_rounded,
                      color: isVerified ? AppColors.gold : AppColors.sokoonGray,
                      size: 12.r,
                    ),
                    3.szW,
                    Flexible(
                      child: AppText(
                        isVerified
                            ? LocaleKeys.ownerHomeVerified
                            : LocaleKeys.ownerHomeUnverified,
                        color: isVerified
                            ? AppColors.gold
                            : AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w600,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        10.szW,
        const NotificationBellButton(role: NotificationRole.owner),
      ],
    );
  }
}
