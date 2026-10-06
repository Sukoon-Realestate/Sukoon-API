import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/property_video.dart';
import 'package:video_player/video_player.dart';

import 'add_property_section_card.dart';

class PropertyVideoPicker extends StatefulWidget {
  const PropertyVideoPicker({
    super.key,
    required this.file,
    required this.existingUrl,
    required this.durationSeconds,
    required this.onVideoSelected,
    required this.onVideoRemoved,
    required this.onPreparingChanged,
  });

  final File? file;
  final String existingUrl;
  final int? durationSeconds;
  final void Function(File file, int durationSeconds) onVideoSelected;
  final VoidCallback onVideoRemoved;
  final ValueChanged<bool> onPreparingChanged;

  @override
  State<PropertyVideoPicker> createState() => _PropertyVideoPickerState();
}

class _PropertyVideoPickerState extends State<PropertyVideoPicker> {
  final ValueNotifier<({bool preparing, String? error})> _selection =
      ValueNotifier((preparing: false, error: null));

  @override
  void dispose() {
    _selection.dispose();
    super.dispose();
  }

  Future<void> _pickVideo({required bool record}) async {
    if (_selection.value.preparing) return;
    _selection.value = (preparing: true, error: null);
    widget.onPreparingChanged(true);
    VideoPlayerController? probe;
    String? error;
    try {
      final File? file = record
          ? await Helpers.recordVideo(
              maxDuration: Validators.propertyVideoMaxDuration,
            )
          : await Helpers.getVideoFromGallery();
      if (!mounted || file == null) return;
      probe = VideoPlayerController.file(file);
      await probe.initialize().timeout(const Duration(seconds: 20));
      if (!mounted) return;
      final Duration duration = probe.value.duration;
      error = Validators.validatePropertyVideoDuration(duration);
      if (error == null) widget.onVideoSelected(file, duration.inSeconds);
    } catch (_) {
      error = LocaleKeys.ownerPropertyVideoFailed;
    } finally {
      await probe?.dispose();
      if (mounted) {
        _selection.value = (preparing: false, error: error);
        widget.onPreparingChanged(false);
      }
    }
  }

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: '${LocaleKeys.ownerPropertyVideoTitle} *',
    child: ValueListenableBuilder<({bool preparing, String? error})>(
      valueListenable: _selection,
      builder: (context, selection, _) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12,
        children: [
          AppText(LocaleKeys.ownerPropertyVideoRequirementDuration),
          if (widget.file != null)
            PropertyVideo.local(
              file: widget.file,
              durationSeconds: widget.durationSeconds,
            )
          else if (widget.existingUrl.isNotEmpty)
            PropertyVideo(
              url: widget.existingUrl,
              durationSeconds: widget.durationSeconds,
            ),
          if (selection.preparing) ...[
            const LinearProgressIndicator(),
            AppText(LocaleKeys.ownerPropertyVideoPreparing),
          ],
          if (selection.error case final error?)
            AppText(error, color: context.appColor(AppColors.red)),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: selection.preparing
                    ? null
                    : () => _pickVideo(record: false),
                icon: const Icon(Icons.video_library_outlined),
                label: AppText(LocaleKeys.ownerPropertyVideoUpload),
              ),
              OutlinedButton.icon(
                onPressed: selection.preparing
                    ? null
                    : () => _pickVideo(record: true),
                icon: const Icon(Icons.videocam_outlined),
                label: AppText(LocaleKeys.ownerPropertyVideoRecord),
              ),
              if (widget.file != null || widget.existingUrl.isNotEmpty)
                TextButton.icon(
                  onPressed: selection.preparing ? null : widget.onVideoRemoved,
                  icon: Icon(
                    Icons.delete_outline_rounded,
                    color: context.appColor(AppColors.red),
                  ),
                  label: AppText(
                    LocaleKeys.ownerPropertyVideoRemove,
                    color: context.appColor(AppColors.red),
                  ),
                ),
            ],
          ),
        ],
      ),
    ),
  );
}
