import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:video_player/video_player.dart';

class VideoPreview extends StatelessWidget {
  const VideoPreview({
    super.key,
    required this.video,
    required this.controller,
    required this.onPlayPressed,
  });

  final OwnerPropertyVideoSelection video;
  final VideoPlayerController? controller;
  final VoidCallback onPlayPressed;

  @override
  Widget build(BuildContext context) {
    final bool isPlaying = controller?.value.isPlaying ?? false;
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          height: 190.h,
          width: double.infinity,
          color: AppColors.sokoonNavy,
          alignment: Alignment.center,
          child: controller == null
              ? Icon(
                  Icons.videocam_outlined,
                  color: AppColors.white,
                  size: 42.r,
                )
              : AspectRatio(
                  aspectRatio: controller!.value.aspectRatio,
                  child: VideoPlayer(controller!),
                ),
        ),
        GestureDetector(
          onTap: onPlayPressed,
          behavior: HitTestBehavior.opaque,
          child: Container(
            width: 54.r,
            height: 54.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.black.withValues(alpha: 0.55),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
              color: AppColors.white,
              size: 30.r,
            ),
          ),
        ),
        PositionedDirectional(
          top: 10.h,
          start: 12.w,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: AppColors.green,
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: AppText(
              LocaleKeys.ownerPropertyVideoUploaded,
              style: AppTextStyles.bold10.copyWith(
                color: AppColors.white,
                fontSize: 10.sp,
                height: 1.45,
              ),
            ),
          ),
        ),
        PositionedDirectional(
          bottom: 10.h,
          start: 12.w,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: AppColors.black.withValues(alpha: 0.65),
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: AppText(
              video.formattedDuration,
              style: AppTextStyles.extraBold.copyWith(
                color: AppColors.white,
                fontSize: 12.sp,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
