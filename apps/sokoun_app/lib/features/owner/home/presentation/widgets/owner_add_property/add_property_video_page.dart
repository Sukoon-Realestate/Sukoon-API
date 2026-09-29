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
import 'add_property_step_shell.dart';

import 'property_video_requirements.dart';
import 'property_video_upload.dart';

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
              fontWeight: FontWeight.w700,
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
        const VideoRequirementsCard(),
        ValueListenableBuilder<
          ({String? validationMessage, bool isPickingVideo, int revision})
        >(
          valueListenable: _uiState,
          builder: (context, uiState, _) => VideoUploadCard(
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
