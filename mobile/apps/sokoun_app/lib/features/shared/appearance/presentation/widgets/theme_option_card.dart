import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import '../cubits/theme_cubit.dart';

class ThemeOptionCard extends StatelessWidget {
  const ThemeOptionCard({
    super.key,
    required this.mode,
    required this.selected,
  });

  final ThemeMode mode;
  final bool selected;

  String get _label => switch (mode) {
    ThemeMode.system => LocaleKeys.appearanceSystem,
    ThemeMode.light => LocaleKeys.appearanceLight,
    ThemeMode.dark => LocaleKeys.appearanceDark,
  };

  IconData get _icon => switch (mode) {
    ThemeMode.system => Icons.brightness_auto_outlined,
    ThemeMode.light => Icons.light_mode_outlined,
    ThemeMode.dark => Icons.dark_mode_outlined,
  };

  @override
  Widget build(BuildContext context) {
    final Color accent = context.appColor(AppColors.sokoonTeal);
    final Duration duration = SokounMotion.duration(context, milliseconds: 180);
    final BorderRadius radius = BorderRadius.circular(14.r);
    return Semantics(
      selected: selected,
      inMutuallyExclusiveGroup: true,
      child: AnimatedContainer(
        duration: duration,
        curve: SokounMotion.curve,
        decoration: BoxDecoration(
          color: context.appColor(
            selected ? AppColors.mintLight : AppColors.white,
            surface: true,
          ),
          borderRadius: radius,
          border: Border.all(
            color: selected ? accent : context.appColor(AppColors.sokoonBorder),
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Material(
          color: AppColors.transparent,
          borderRadius: radius,
          child: InkWell(
            borderRadius: radius,
            onTap: () => context.read<ThemeCubit>().setMode(mode),
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 18.h),
              child: Row(
                spacing: 14.w,
                children: [
                  Icon(_icon, color: accent, size: 24.r),
                  Expanded(
                    child: AppText(
                      _label,
                      style: AppTextStyles.bold16.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                      ),
                    ),
                  ),
                  ExcludeSemantics(
                    child: AnimatedScale(
                      scale: selected ? 1 : .85,
                      duration: duration,
                      curve: SokounMotion.curve,
                      child: Icon(
                        selected
                            ? Icons.check_circle_rounded
                            : Icons.circle_outlined,
                        color: selected
                            ? accent
                            : context.appColor(AppColors.sokoonMuted),
                        size: 24.r,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
