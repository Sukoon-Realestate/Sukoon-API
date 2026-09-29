import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import 'share_action_row.dart';

class TenantPropertyShareSheet extends StatelessWidget {
  const TenantPropertyShareSheet({super.key, required this.shareUrl});

  final String shareUrl;

  Future<void> _copyLink(BuildContext context) async {
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    await Clipboard.setData(ClipboardData(text: shareUrl));
    Go.back();
    messenger.showSnackBar(
      SnackBar(content: Text(LocaleKeys.tenantPropertyDetailsLinkCopied)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 26.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 42.w,
              height: 4.h,
              decoration: BoxDecoration(
                color: AppColors.grayPale,
                borderRadius: BorderRadius.circular(999.r),
              ),
            ).centerWidget,
            18.szH,
            AppText(
              LocaleKeys.tenantPropertyDetailsShareTitle,
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.start,
            ),
            14.szH,
            TenantPropertyShareActionRow(
              icon: Icons.link_rounded,
              label: LocaleKeys.tenantPropertyDetailsCopyLink,
              color: AppColors.sokoonTeal,
              onActionPressed: () => _copyLink(context),
            ),
            8.szH,
            TenantPropertyShareActionRow(
              icon: Icons.ios_share_rounded,
              label: LocaleKeys.tenantPropertyDetailsShare,
              color: AppColors.blue,
              onActionPressed: Go.back,
            ),
            8.szH,
            TenantPropertyShareActionRow(
              icon: Icons.close_rounded,
              label: LocaleKeys.cancel,
              color: AppColors.sokoonRose,
              onActionPressed: Go.back,
            ),
          ],
        ),
      ),
    );
  }
}
