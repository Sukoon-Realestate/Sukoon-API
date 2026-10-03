import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';

import 'sokoun_motion.dart';

class SokounRefreshIndicator extends StatelessWidget {
  const SokounRefreshIndicator({super.key, required this.status});

  final RefreshIndicatorStatus? status;

  static Widget builder(BuildContext context, RefreshIndicatorStatus? status) =>
      SokounRefreshIndicator(status: status);

  @override
  Widget build(BuildContext context) {
    final bool visible = switch (status) {
      RefreshIndicatorStatus.drag ||
      RefreshIndicatorStatus.armed ||
      RefreshIndicatorStatus.snap ||
      RefreshIndicatorStatus.refresh => true,
      _ => false,
    };
    final bool armed = status == RefreshIndicatorStatus.armed;
    final bool loading = switch (status) {
      RefreshIndicatorStatus.snap ||
      RefreshIndicatorStatus.refresh ||
      RefreshIndicatorStatus.done => true,
      _ => false,
    };
    final Duration duration = SokounMotion.duration(context, milliseconds: 180);
    final String label = loading
        ? LocaleKeys.pullRefreshLoading
        : armed
        ? LocaleKeys.pullRefreshRelease
        : LocaleKeys.pullRefreshHint;

    return ExcludeSemantics(
      excluding: !visible,
      child: AnimatedSlide(
        offset: visible ? Offset.zero : const Offset(0, -.2),
        duration: duration,
        curve: SokounMotion.curve,
        child: AnimatedOpacity(
          opacity: visible ? 1 : 0,
          duration: duration,
          curve: SokounMotion.curve,
          child: Align(
            alignment: Alignment.topCenter,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
              child: Semantics(
                container: true,
                liveRegion: true,
                label: label,
                excludeSemantics: true,
                child: Container(
                  constraints: BoxConstraints(maxWidth: 280.w),
                  padding: EdgeInsets.symmetric(
                    horizontal: 12.w,
                    vertical: 8.h,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.white,
                    borderRadius: BorderRadius.circular(999.r),
                    border: Border.all(color: AppColors.tealAlpha19),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.shadowBlack04,
                        blurRadius: 12.r,
                        offset: Offset(0, 4.h),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    spacing: 10.w,
                    children: [
                      Container(
                        width: 36.r,
                        height: 36.r,
                        decoration: const BoxDecoration(
                          color: AppColors.mintLight,
                          shape: BoxShape.circle,
                        ),
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            if (loading && visible && duration != Duration.zero)
                              Positioned.fill(
                                child: CircularProgressIndicator(
                                  color: AppColors.sokoonTeal,
                                ),
                              ),
                            if (loading)
                              AppLogoWidget(size: 25.sp)
                            else
                              AnimatedRotation(
                                turns: armed ? .5 : 0,
                                duration: duration,
                                curve: SokounMotion.curve,
                                child: Icon(
                                  Icons.arrow_downward_rounded,
                                  size: 20.r,
                                  color: AppColors.sokoonTeal,
                                ),
                              ),
                          ],
                        ),
                      ),
                      Flexible(
                        child: AppText(
                          label,
                          style: AppTextStyles.medium13.copyWith(
                            color: AppColors.sokoonNavy,
                            height: 1.45,
                          ),
                          textAlign: TextAlign.start,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
