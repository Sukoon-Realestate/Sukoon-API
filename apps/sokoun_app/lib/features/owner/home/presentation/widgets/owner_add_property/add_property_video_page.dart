import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:video_player/video_player.dart';

import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyVideoPage extends StatefulWidget {
  const AddPropertyVideoPage({
    super.key,
    required this.video,
    required this.onVideoSelected,
    required this.onVideoRemoved,
    required this.onNext,
    required this.onSkip,
    required this.onBack,
  });

  final OwnerPropertyVideoSelection? video;
  final ValueChanged<OwnerPropertyVideoSelection> onVideoSelected;
  final VoidCallback onVideoRemoved;
  final VoidCallback onNext;
  final VoidCallback onSkip;
  final VoidCallback onBack;

  @override
  State<AddPropertyVideoPage> createState() => _AddPropertyVideoPageState();
}

class _AddPropertyVideoPageState extends State<AddPropertyVideoPage> {
  static const Duration _maximumDuration = Duration(seconds: 60);

  VideoPlayerController? _videoController;
  String? _previewPath;
  int _previewGeneration = 0;
  final ValueNotifier<
    ({String? validationMessage, bool isPickingVideo, int revision})
  >
  _uiState =
      ValueNotifier<
        ({String? validationMessage, bool isPickingVideo, int revision})
      >((validationMessage: null, isPickingVideo: false, revision: 0));

  @override
  void initState() {
    super.initState();
    unawaited(_setPreview(widget.video));
  }

  @override
  void didUpdateWidget(covariant AddPropertyVideoPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    final String? nextPath = widget.video?.file.path;
    if (nextPath != oldWidget.video?.file.path && nextPath != _previewPath) {
      unawaited(_setPreview(widget.video));
    }
  }

  @override
  void dispose() {
    _previewGeneration++;
    _videoController?.dispose();
    _uiState.dispose();
    super.dispose();
  }

  void _updateUi({
    String? validationMessage,
    bool clearValidation = false,
    bool? isPickingVideo,
  }) {
    final current = _uiState.value;
    _uiState.value = (
      validationMessage: clearValidation
          ? null
          : validationMessage ?? current.validationMessage,
      isPickingVideo: isPickingVideo ?? current.isPickingVideo,
      revision: current.revision + 1,
    );
  }

  Future<void> _setPreview(OwnerPropertyVideoSelection? selection) async {
    final int generation = ++_previewGeneration;
    final VideoPlayerController? previousController = _videoController;
    if (selection == null) {
      _videoController = null;
      _previewPath = null;
      await previousController?.dispose();
      if (mounted && generation == _previewGeneration) {
        _updateUi();
      }
      return;
    }

    final VideoPlayerController controller = VideoPlayerController.file(
      selection.file,
    );
    try {
      await controller.initialize();
    } catch (_) {
      await controller.dispose();
      if (mounted && generation == _previewGeneration) {
        _updateUi(validationMessage: LocaleKeys.ownerPropertyVideoFailed);
      }
      return;
    }
    if (!mounted || generation != _previewGeneration) {
      await controller.dispose();
      return;
    }
    _videoController = controller;
    _previewPath = selection.file.path;
    await previousController?.dispose();
    if (mounted) {
      _updateUi();
    }
  }

  Future<void> _pickVideo({required bool fromCamera}) async {
    if (_uiState.value.isPickingVideo) {
      return;
    }
    _updateUi(isPickingVideo: true, clearValidation: true);

    try {
      final File? file = fromCamera
          ? await Helpers.recordVideo(maxDuration: _maximumDuration)
          : await Helpers.getVideoFromGallery();
      if (!mounted || file == null) {
        return;
      }

      final VideoPlayerController controller = VideoPlayerController.file(file);
      try {
        await controller.initialize();
      } catch (_) {
        await controller.dispose();
        rethrow;
      }
      if (!mounted) {
        await controller.dispose();
        return;
      }

      final Duration duration = controller.value.duration;
      if (duration > _maximumDuration) {
        await controller.dispose();
        _updateUi(validationMessage: LocaleKeys.ownerPropertyVideoTooLong);
        return;
      }

      final VideoPlayerController? previousController = _videoController;
      _videoController = controller;
      _previewPath = file.path;
      await previousController?.dispose();
      widget.onVideoSelected(
        OwnerPropertyVideoSelection(file: file, duration: duration),
      );
    } catch (_) {
      if (mounted) {
        _updateUi(validationMessage: LocaleKeys.ownerPropertyVideoFailed);
      }
    } finally {
      if (mounted) {
        _updateUi(isPickingVideo: false);
      }
    }
  }

  Future<void> _togglePlayback() async {
    final VideoPlayerController? controller = _videoController;
    if (controller == null || !controller.value.isInitialized) {
      return;
    }
    if (controller.value.isPlaying) {
      await controller.pause();
    } else {
      await controller.play();
    }
    if (mounted) {
      _updateUi();
    }
  }

  void _removeVideo() {
    _updateUi(clearValidation: true);
    widget.onVideoRemoved();
  }

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyVideoSelection? video = widget.video;

    return AddPropertyStepShell(
      title: LocaleKeys.ownerPropertyVideoTitle,
      activeSegments: 3,
      segmentCount: 5,
      progressSubtitle: LocaleKeys.ownerPropertyVideoStepProgress,
      primaryLabel: LocaleKeys.ownerPropertyVideoNextPricing,
      onPrimaryTap: video == null ? null : widget.onNext,
      secondaryLabel: LocaleKeys.ownerPropertyVideoSkip,
      onSecondaryTap: widget.onSkip,
      onBack: widget.onBack,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(
              LocaleKeys.ownerPropertyVideoTitle,
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.start,
            ),
            4.szH,
            AppText(
              LocaleKeys.ownerPropertyVideoSubtitle,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w400,
              textAlign: TextAlign.start,
            ),
          ],
        ),
        const _VideoRequirementsCard(),
        ValueListenableBuilder<
          ({String? validationMessage, bool isPickingVideo, int revision})
        >(
          valueListenable: _uiState,
          builder: (context, uiState, _) => _VideoUploadCard(
            video: video,
            controller: _videoController,
            isPickingVideo: uiState.isPickingVideo,
            validationMessage: uiState.validationMessage,
            onRecordPressed: () => _pickVideo(fromCamera: true),
            onUploadPressed: () => _pickVideo(fromCamera: false),
            onPlayPressed: _togglePlayback,
            onRemovePressed: _removeVideo,
          ),
        ),
        AddPropertyInfoBanner(
          text: LocaleKeys.ownerPropertyVideoPrivacyHint,
          backgroundColor: AppColors.mintPale,
          borderColor: AppColors.tealAlpha19,
          iconColor: AppColors.sokoonTeal,
          textColor: AppColors.sokoonTeal,
          icon: Icons.shield_outlined,
        ),
      ],
    );
  }
}

class _VideoRequirementsCard extends StatelessWidget {
  const _VideoRequirementsCard();

  @override
  Widget build(BuildContext context) {
    final List<String> requirements = [
      LocaleKeys.ownerPropertyVideoRequirementDuration,
      LocaleKeys.ownerPropertyVideoRequirementRooms,
      LocaleKeys.ownerPropertyVideoRequirementStable,
      LocaleKeys.ownerPropertyVideoRequirementPrivacy,
    ];

    return AddPropertySectionCard(
      title: LocaleKeys.ownerPropertyVideoRequirements,
      child: Column(
        children: [
          for (int index = 0; index < requirements.length; index++) ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.check_rounded,
                  color: AppColors.sokoonTeal,
                  size: 16.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    requirements[index],
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w400,
                    textAlign: TextAlign.start,
                    maxLines: 2,
                  ),
                ),
              ],
            ),
            if (index < requirements.length - 1) ...[
              8.szH,
              const Divider(height: 1, color: AppColors.sokoonBorder),
              8.szH,
            ],
          ],
          12.szH,
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 9.h),
            decoration: BoxDecoration(
              color: AppColors.orangePale,
              borderRadius: BorderRadius.circular(10.r),
              border: Border.all(color: AppColors.goldAlpha15),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.schedule_rounded,
                  color: AppColors.brown,
                  size: 16.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    LocaleKeys.ownerPropertyVideoMaximumDuration,
                    color: AppColors.brown,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w700,
                    textAlign: TextAlign.start,
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

class _VideoUploadCard extends StatelessWidget {
  const _VideoUploadCard({
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
            _VideoLoadingState()
          else if (hasVideo)
            _VideoPreview(
              video: video!,
              controller: hasPreview ? controller : null,
              onPlayPressed: onPlayPressed,
            )
          else
            _VideoEmptyState(
              onRecordPressed: onRecordPressed,
              onUploadPressed: onUploadPressed,
            ),
          if (validationMessage != null)
            _VideoErrorMessage(message: validationMessage!),
          if (hasVideo && !isPickingVideo)
            Padding(
              padding: EdgeInsets.all(14.w),
              child: Row(
                children: [
                  Expanded(
                    child: _VideoActionButton(
                      label: LocaleKeys.ownerPropertyVideoChange,
                      icon: Icons.refresh_rounded,
                      color: AppColors.sokoonTeal,
                      onTap: onUploadPressed,
                    ),
                  ),
                  10.szW,
                  Expanded(
                    child: _VideoActionButton(
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

class _VideoEmptyState extends StatelessWidget {
  const _VideoEmptyState({
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
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
            fontWeight: FontWeight.w800,
            textAlign: TextAlign.center,
          ),
          5.szH,
          AppText(
            LocaleKeys.ownerPropertyVideoMaximumDuration,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            textAlign: TextAlign.center,
          ),
          18.szH,
          Row(
            children: [
              Expanded(
                child: _VideoActionButton(
                  label: LocaleKeys.ownerPropertyVideoRecord,
                  icon: Icons.radio_button_checked_rounded,
                  color: AppColors.sokoonTeal,
                  filled: true,
                  onTap: onRecordPressed,
                ),
              ),
              10.szW,
              Expanded(
                child: _VideoActionButton(
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

class _VideoLoadingState extends StatelessWidget {
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
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}

class _VideoPreview extends StatelessWidget {
  const _VideoPreview({
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
              color: AppColors.white,
              fontSize: 10.sp,
              fontWeight: FontWeight.w700,
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
              color: AppColors.white,
              fontSize: 12.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ],
    );
  }
}

class _VideoErrorMessage extends StatelessWidget {
  const _VideoErrorMessage({required this.message});

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
              color: AppColors.red,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.start,
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}

class _VideoActionButton extends StatelessWidget {
  const _VideoActionButton({
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
                color: filled ? AppColors.white : color,
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
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
