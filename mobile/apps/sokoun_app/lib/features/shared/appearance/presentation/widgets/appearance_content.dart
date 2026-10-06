import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../cubits/theme_cubit.dart';
import 'theme_option_card.dart';

class AppearanceContent extends StatelessWidget {
  const AppearanceContent({super.key});

  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.all(20.r),
    children: [
      AppText(
        LocaleKeys.appearanceDescription,
        style: AppTextStyles.regular14.copyWith(
          color: context.appColor(AppColors.sokoonGray),
          height: 1.5,
        ),
      ),
      24.szH,
      BlocBuilder<ThemeCubit, ThemeMode>(
        builder: (context, selected) => Column(
          spacing: 12.h,
          children: [
            for (final mode in ThemeMode.values)
              ThemeOptionCard(mode: mode, selected: mode == selected),
          ],
        ),
      ),
    ],
  );
}
