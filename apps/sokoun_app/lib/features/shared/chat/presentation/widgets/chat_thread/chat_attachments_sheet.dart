import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/chat/data/enums/chat_attachment_type.dart';

class ChatAttachmentsSheet extends StatelessWidget {
  const ChatAttachmentsSheet({super.key, required this.onAttachmentSelected});

  final void Function(ChatAttachmentType type) onAttachmentSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(24.w, 12.h, 24.w, 16.h),
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
              width: 36.w,
              height: 4.h,
              decoration: BoxDecoration(
                color: AppColors.sokoonBorder,
                borderRadius: BorderRadius.circular(2.r),
              ),
            ).centerWidget,
            22.szH,
            AppText(
              LocaleKeys.chatSendAttachment,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              fontWeight: FontWeight.w900,
            ),
            20.szH,
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                for (final type in ChatAttachmentType.values)
                  _AttachmentAction(
                    type: type,
                    onPressed: () => onAttachmentSelected(type),
                  ),
              ],
            ),
            24.szH,
            DefaultButton(
              key: const ValueKey('chat-attachment-cancel'),
              onTap: () => Go.back(),
              title: LocaleKeys.cancel,
              color: AppColors.white,
              textColor: AppColors.sokoonNavy,
              borderColor: AppColors.sokoonBorder,
              borderRadius: BorderRadius.circular(16.r),
              width: double.infinity,
              height: 50.h,
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ),
    );
  }
}

class _AttachmentAction extends StatelessWidget {
  const _AttachmentAction({required this.type, required this.onPressed});

  final ChatAttachmentType type;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      key: ValueKey('chat-attachment-${type.name}'),
      onTap: onPressed,
      borderRadius: BorderRadius.circular(18.r),
      child: SizedBox(
        width: 72.w,
        child: Column(
          children: [
            Container(
              width: 60.r,
              height: 60.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: _backgroundColor,
                borderRadius: BorderRadius.circular(18.r),
              ),
              child: Icon(_icon, color: _color, size: 26.r),
            ),
            8.szH,
            AppText(
              _label,
              color: AppColors.sokoonNavy,
              fontSize: 11.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  IconData get _icon {
    if (type.isCamera) {
      return Icons.camera_alt_outlined;
    }
    if (type.isPhotos) {
      return Icons.photo_library_outlined;
    }
    if (type.isFile) {
      return Icons.insert_drive_file_outlined;
    }
    return Icons.location_on_outlined;
  }

  Color get _color {
    if (type.isCamera) {
      return AppColors.sokoonTeal;
    }
    if (type.isPhotos) {
      return AppColors.blue;
    }
    if (type.isFile) {
      return AppColors.sokoonGold;
    }
    return AppColors.red;
  }

  Color get _backgroundColor {
    if (type.isCamera) {
      return AppColors.mintLight;
    }
    if (type.isPhotos) {
      return AppColors.bluePale;
    }
    if (type.isFile) {
      return AppColors.goldPale;
    }
    return AppColors.redPale;
  }

  String get _label {
    if (type.isCamera) {
      return LocaleKeys.camera;
    }
    if (type.isPhotos) {
      return LocaleKeys.chatPhotos;
    }
    if (type.isFile) {
      return LocaleKeys.chatFile;
    }
    return LocaleKeys.chatLocation;
  }
}
