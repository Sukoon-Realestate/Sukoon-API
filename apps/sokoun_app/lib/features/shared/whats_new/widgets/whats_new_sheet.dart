import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

Future<void> showWhatsNewSheet({
  required List<String> items,
  required String version,
}) async {
  await showModalBottomSheet<void>(
    context: Go.context,
    isScrollControlled: true,
    backgroundColor: AppColors.transparent,
    barrierColor: AppColors.black.withValues(alpha: 0.45),
    builder: (_) => WhatsNewSheet(items: items, version: version),
  );
}

class WhatsNewSheet extends StatelessWidget {
  const WhatsNewSheet({required this.items, required this.version, super.key});

  final List<String> items;
  final String version;

  @override
  Widget build(BuildContext context) {
    final double maxHeight = MediaQuery.sizeOf(context).height * 0.88;

    return SafeArea(
      top: false,
      child: Align(
        alignment: Alignment.bottomCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: maxHeight),
          child: Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
              boxShadow: [
                BoxShadow(
                  color: AppColors.black.withValues(alpha: 0.12),
                  blurRadius: 32.r,
                  offset: Offset(0, -4.h),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const _SheetChrome(),
                Flexible(
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 16.h),
                    child: Column(
                      children: [
                        _WhatsNewHeader(version: version),
                        20.szH,
                        const Divider(
                          height: 1,
                          thickness: 1,
                          color: AppColors.border,
                        ),
                        20.szH,
                        _FeaturesList(items: items),
                      ],
                    ),
                  ),
                ),
                const Divider(height: 1, thickness: 1, color: AppColors.border),
                DefaultButton(
                  width: double.infinity,
                  height: 50.h,
                  borderRadius: BorderRadius.circular(50.r),
                  color: AppColors.primary,
                  title: LocaleKeys.whatsNewStartNow,
                  textStyle: AppTextStyles.bold15.copyWith(
                    fontSize: 15.sp,
                    height: 1.45,
                  ),
                  onTap: Go.back,
                ).paddingSymmetric(horizontal: 20.w, vertical: 10.h),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SheetChrome extends StatelessWidget {
  const _SheetChrome();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 36.h,
      child: Align(
        alignment: Alignment.topCenter,
        child: Container(
          width: 40.w,
          height: 4.h,
          margin: EdgeInsets.only(top: 12.h),
          decoration: BoxDecoration(
            color: const Color(0xFFDDDDDD),
            borderRadius: BorderRadius.circular(50.r),
          ),
        ),
      ),
    );
  }
}

class _WhatsNewHeader extends StatelessWidget {
  const _WhatsNewHeader({required this.version});

  final String version;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 52.r,
          height: 52.r,
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: Color(0xFFE8F4F0),
            shape: BoxShape.circle,
          ),
          child: AppText(
            '🎉',
            style: AppTextStyles.regular.copyWith(fontSize: 24.sp),
          ),
        ),
        8.szH,
        AppText(
          LocaleKeys.whatsNewTitle,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.textBlack,
            fontSize: 18.sp,
            height: 1.3,
          ),
          textAlign: TextAlign.center,
        ),
        4.szH,
        Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 3.h),
          decoration: BoxDecoration(
            color: AppColors.mintPale,
            borderRadius: BorderRadius.circular(50.r),
          ),
          child: AppText(
            '${LocaleKeys.whatsNewVersionLabel} $version',
            style: AppTextStyles.medium11.copyWith(
              color: AppColors.primary,
              fontSize: 11.sp,
              height: 1.45,
            ),
          ),
        ),
        8.szH,
        ConstrainedBox(
          constraints: BoxConstraints(maxWidth: 280.w),
          child: AppText(
            LocaleKeys.whatsNewDescription,
            style: AppTextStyles.regular13.copyWith(
              color: AppColors.darkGay,
              fontSize: 13.sp,
              height: 1.7,
            ),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}

class _FeaturesList extends StatelessWidget {
  const _FeaturesList({required this.items});

  final List<String> items;

  static const List<_FeatureVisual> _visuals = [
    _FeatureVisual(
      icon: Icons.bolt_rounded,
      backgroundColor: AppColors.mintPale,
      foregroundColor: AppColors.primary,
    ),
    _FeatureVisual(
      icon: Icons.auto_awesome_rounded,
      backgroundColor: AppColors.bluePale,
      foregroundColor: AppColors.blue,
    ),
    _FeatureVisual(
      icon: Icons.build_rounded,
      backgroundColor: AppColors.greenPale,
      foregroundColor: AppColors.green,
    ),
    _FeatureVisual(
      icon: Icons.notifications_none_rounded,
      backgroundColor: AppColors.redPale,
      foregroundColor: AppColors.rose,
    ),
    _FeatureVisual(
      icon: Icons.lock_outline_rounded,
      backgroundColor: Color(0xFFF5F3FF),
      foregroundColor: Color(0xFF6D28D9),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: items.indexed
          .map(
            ((int, String) entry) => _FeatureItem(
              title: entry.$2,
              visual: _visuals[entry.$1 % _visuals.length],
            ).paddingOnly(bottom: entry.$1 == items.length - 1 ? 0 : 16.h),
          )
          .toList(),
    );
  }
}

class _FeatureItem extends StatelessWidget {
  const _FeatureItem({required this.title, required this.visual});

  final String title;
  final _FeatureVisual visual;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40.r,
          height: 40.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: visual.backgroundColor,
            shape: BoxShape.circle,
          ),
          child: Icon(visual.icon, size: 19.r, color: visual.foregroundColor),
        ),
        12.szW,
        Expanded(
          child: AppText(
            title,
            style: AppTextStyles.bold14.copyWith(
              color: AppColors.textBlack,
              fontSize: 14.sp,
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}

class _FeatureVisual {
  const _FeatureVisual({
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
}
