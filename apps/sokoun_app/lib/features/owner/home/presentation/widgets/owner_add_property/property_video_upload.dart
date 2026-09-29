import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:video_player/video_player.dart';

import 'property_video_preview.dart';

class VideoUploadCard extends StatelessWidget {
  const VideoUploadCard({
    super.key,
    required this.video,
    required this.controller,
    required this.isPickingVideo,
    required this.validationMessage,
    required this.onRecordPressed,
    required this.onUploadPressed,
    required this.onPlayPressed,
    required this.onRemovePressed,
  });

  final OwnerPropertyVideoSelection? video;
  final VideoPlayerController? controller;
  final bool isPickingVideo;
  final String? validationMessage;
  final VoidCallback onRecordPressed;
  final VoidCallback onUploadPressed;
  final VoidCallback onPlayPressed;
  final VoidCallback onRemovePressed;

  @override
  Widget build(BuildContext context) {
    final bool hasVideo = video != null;
    final bool hasPreview = controller?.value.isInitialized ?? false;

    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(
          color: validationMessage == null
              ? AppColors.sokoonBorder
              : AppColors.red,
          width: hasVideo ? 1 : 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (isPickingVideo)
            VideoLoadingState()
          else if (hasVideo)
            VideoPreview(
              video: video!,
              controller: hasPreview ? controller : null,
              onPlayPressed: onPlayPressed,
            )
          else
            VideoEmptyState(
              onRecordPressed: onRecordPressed,
              onUploadPressed: onUploadPressed,
            ),
          if (validationMessage != null)
            VideoErrorMessage(message: validationMessage!),
          if (hasVideo && !isPickingVideo)
            Padding(
              padding: EdgeInsets.all(14.w),
              child: Row(
                children: [
                  Expanded(
                    child: VideoActionButton(
                      label: LocaleKeys.ownerPropertyVideoChange,
                      icon: Icons.refresh_rounded,
                      color: AppColors.sokoonTeal,
                      onTap: onUploadPressed,
                    ),
                  ),
                  10.szW,
                  Expanded(
                    child: VideoActionButton(
                      label: LocaleKeys.ownerPropertyVideoRemove,
                      icon: Icons.delete_outline_rounded,
                      color: AppColors.red,
                      onTap: onRemovePressed,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class VideoEmptyState extends StatelessWidget {
  const VideoEmptyState({
    super.key,
    required this.onRecordPressed,
    required this.onUploadPressed,
  });

  final VoidCallback onRecordPressed;
  final VoidCallback onUploadPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 30.h),
      decoration: BoxDecoration(
        color: AppColors.grayOffWhite,
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        children: [
          Container(
            width: 64.r,
            height: 64.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.grayBackground,
              borderRadius: BorderRadius.circular(20.r),
            ),
            child: Icon(
              Icons.videocam_outlined,
              color: AppColors.sokoonMuted,
              size: 30.r,
            ),
          ),
          14.szH,
          AppText(
            LocaleKeys.ownerPropertyVideoUploadOrRecord,
            style: AppTextStyles.extraBold15.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 15.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
          ),
          5.szH,
          AppText(
            LocaleKeys.ownerPropertyVideoMaximumDuration,
            style: AppTextStyles.regular12.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
          ),
          18.szH,
          Row(
            children: [
              Expanded(
                child: VideoActionButton(
                  label: LocaleKeys.ownerPropertyVideoRecord,
                  icon: Icons.radio_button_checked_rounded,
                  color: AppColors.sokoonTeal,
                  filled: true,
                  onTap: onRecordPressed,
                ),
              ),
              10.szW,
              Expanded(
                child: VideoActionButton(
                  label: LocaleKeys.ownerPropertyVideoUpload,
                  icon: Icons.file_upload_outlined,
                  color: AppColors.sokoonNavy,
                  onTap: onUploadPressed,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class VideoLoadingState extends StatelessWidget {
  const VideoLoadingState({super.key});
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 220.h,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 34.r,
            height: 34.r,
            child: const CircularProgressIndicator(
              strokeWidth: 3,
              color: AppColors.sokoonTeal,
            ),
          ),
          12.szH,
          AppText(
            LocaleKeys.ownerPropertyVideoPreparing,
            style: AppTextStyles.bold13.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}

class VideoErrorMessage extends StatelessWidget {
  const VideoErrorMessage({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      color: AppColors.red.withValues(alpha: 0.06),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, color: AppColors.red, size: 18.r),
          8.szW,
          Expanded(
            child: AppText(
              message,
              style: AppTextStyles.bold12.copyWith(
                color: AppColors.red,
                fontSize: 12.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.start,
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}

class VideoActionButton extends StatelessWidget {
  const VideoActionButton({
    super.key,
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
    this.filled = false,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 44.h,
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(horizontal: 10.w),
        decoration: BoxDecoration(
          color: filled ? color : AppColors.white,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(color: filled ? color : AppColors.sokoonBorder),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: filled ? AppColors.white : color, size: 17.r),
            7.szW,
            Flexible(
              child: AppText(
                label,
                style: AppTextStyles.bold12.copyWith(
                  color: filled ? AppColors.white : color,
                  fontSize: 12.sp,
                  height: 1.45,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
