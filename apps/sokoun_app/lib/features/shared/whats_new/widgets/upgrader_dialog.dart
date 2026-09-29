import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:upgrader/upgrader.dart';

class AppUpgradeAlert extends UpgradeAlert {
  AppUpgradeAlert({
    required Upgrader upgrader,
    required this.onUpdatePressed,
    required Widget child,
    super.key,
  }) : super(
         upgrader: upgrader,
         barrierDismissible: false,
         showIgnore: false,
         showPrompt: false,
         showReleaseNotes: false,
         shouldPopScope: () => !upgrader.blocked(),
         child: child,
       );

  final Future<void> Function() onUpdatePressed;

  @override
  UpgradeAlertState createState() => _AppUpgradeAlertState();
}

class _AppUpgradeAlertState extends UpgradeAlertState {
  AppUpgradeAlert get _alert => widget as AppUpgradeAlert;

  @override
  Widget alertDialog(
    Key? key,
    String title,
    String message,
    String? releaseNotes,
    BuildContext context,
    bool cupertino,
    UpgraderMessages messages,
  ) {
    final bool isRequired = widget.upgrader.blocked();
    final String version = widget.upgrader.currentAppStoreVersion ?? '';

    return UpgraderDialog(
      key: key,
      isRequired: isRequired,
      version: version,
      onClosePressed: isRequired ? null : () => onUserLater(context, true),
      onUpdatePressed: () async {
        await _alert.onUpdatePressed();
        if (!isRequired && context.mounted) {
          popNavigator(context);
        }
      },
    );
  }

  @override
  void popNavigator(BuildContext context) {
    Go.back();
    displayed = false;
  }
}

class UpgraderDialog extends StatefulWidget {
  const UpgraderDialog({
    required this.isRequired,
    required this.version,
    required this.onUpdatePressed,
    required this.onClosePressed,
    super.key,
  });

  final bool isRequired;
  final String version;
  final Future<void> Function() onUpdatePressed;
  final void Function()? onClosePressed;

  @override
  State<UpgraderDialog> createState() => _UpgraderDialogState();
}

class _UpgraderDialogState extends State<UpgraderDialog> {
  final ValueNotifier<bool> _isOpeningStore = ValueNotifier<bool>(false);

  Future<void> _openStore() async {
    if (_isOpeningStore.value) return;

    _isOpeningStore.value = true;
    try {
      await widget.onUpdatePressed();
    } finally {
      if (mounted) {
        _isOpeningStore.value = false;
      }
    }
  }

  @override
  void dispose() {
    _isOpeningStore.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final String title = widget.isRequired
        ? LocaleKeys.updateDialogRequiredTitle
        : LocaleKeys.updateDialogOptionalTitle;
    final String description = widget.isRequired
        ? LocaleKeys.updateDialogRequiredDescription
        : LocaleKeys.updateDialogOptionalDescription;

    return Dialog(
      elevation: 0,
      insetPadding: EdgeInsets.symmetric(horizontal: 24.w),
      backgroundColor: AppColors.transparent,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: 340.w),
        child: Semantics(
          container: true,
          label: title,
          child: Container(
            width: double.infinity,
            padding: EdgeInsets.fromLTRB(24.w, 28.h, 24.w, 24.h),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(16.r),
              boxShadow: [
                BoxShadow(
                  color: AppColors.black.withValues(alpha: 0.18),
                  blurRadius: 40.r,
                  offset: Offset(0, 8.h),
                ),
              ],
            ),
            child: Stack(
              children: [
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const _UpdateIcon(),
                    16.szH,
                    AppText(
                      title,
                      color: AppColors.textBlack,
                      fontSize: 18.sp,
                      fontWeight: FontWeight.bold,
                      textAlign: TextAlign.center,
                      height: 1.3,
                    ),
                    8.szH,
                    AppText(
                      description,
                      color: AppColors.darkGay,
                      fontSize: 13.sp,
                      textAlign: TextAlign.center,
                      height: 1.8,
                    ),
                    16.szH,
                    _VersionBadge(version: widget.version),
                    20.szH,
                    ValueListenableBuilder<bool>(
                      valueListenable: _isOpeningStore,
                      builder: (context, isOpeningStore, _) => _UpdateButton(
                        isLoading: isOpeningStore,
                        onUpdatePressed: _openStore,
                      ),
                    ),
                    if (!widget.isRequired) ...[
                      12.szH,
                      _LaterButton(onLaterPressed: widget.onClosePressed!),
                    ],
                  ],
                ),
                if (!widget.isRequired)
                  PositionedDirectional(
                    top: -14.h,
                    end: -14.w,
                    child: IconButton(
                      tooltip: LocaleKeys.updateDialogClose,
                      onPressed: widget.onClosePressed,
                      visualDensity: VisualDensity.compact,
                      icon: Icon(
                        Icons.close_rounded,
                        size: 22.r,
                        color: AppColors.grayLight,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _UpdateIcon extends StatelessWidget {
  const _UpdateIcon();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 60.r,
      height: 60.r,
      alignment: Alignment.center,
      decoration: const BoxDecoration(
        color: AppColors.mintPale,
        shape: BoxShape.circle,
      ),
      child: Icon(
        Icons.file_download_outlined,
        size: 28.r,
        color: AppColors.primary,
      ),
    );
  }
}

class _VersionBadge extends StatelessWidget {
  const _VersionBadge({required this.version});

  final String version;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: AppColors.grayBackground,
        borderRadius: BorderRadius.circular(50.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AppText(
            '${LocaleKeys.updateDialogNewVersion}:',
            color: AppColors.darkGay,
            fontSize: 11.sp,
          ),
          6.szW,
          AppText(
            version,
            color: AppColors.primary,
            fontSize: 11.sp,
            fontWeight: FontWeight.bold,
          ),
        ],
      ),
    );
  }
}

class _UpdateButton extends StatelessWidget {
  const _UpdateButton({required this.isLoading, required this.onUpdatePressed});

  final bool isLoading;
  final void Function() onUpdatePressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 50.h,
      child: ElevatedButton(
        onPressed: isLoading ? null : onUpdatePressed,
        style: ElevatedButton.styleFrom(
          elevation: 0,
          backgroundColor: AppColors.primary,
          disabledBackgroundColor: AppColors.tealAlpha80,
          foregroundColor: AppColors.white,
          disabledForegroundColor: AppColors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(50.r),
          ),
        ),
        child: AnimatedSwitcher(
          duration: SokounMotion.duration(context, milliseconds: 200),
          child: isLoading
              ? Row(
                  key: const ValueKey('update-loading'),
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox.square(
                      dimension: 16.r,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.r,
                        color: AppColors.white,
                        backgroundColor: AppColors.white.withValues(alpha: 0.4),
                      ),
                    ),
                    8.szW,
                    Flexible(
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: AppText(
                          LocaleKeys.updateDialogOpeningStore,
                          color: AppColors.white,
                          fontSize: 15.sp,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                )
              : FittedBox(
                  key: const ValueKey('update-idle'),
                  fit: BoxFit.scaleDown,
                  child: AppText(
                    LocaleKeys.updateDialogUpdateNow,
                    color: AppColors.white,
                    fontSize: 15.sp,
                    fontWeight: FontWeight.bold,
                  ),
                ),
        ),
      ),
    );
  }
}

class _LaterButton extends StatelessWidget {
  const _LaterButton({required this.onLaterPressed});

  final void Function() onLaterPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 46.h,
      child: OutlinedButton(
        onPressed: onLaterPressed,
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.darkGay,
          side: BorderSide(color: AppColors.border, width: 1.5.w),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(50.r),
          ),
        ),
        child: AppText(
          LocaleKeys.updateDialogLater,
          color: AppColors.darkGay,
          fontSize: 14.sp,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
