import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:package_info_plus/package_info_plus.dart';

class AboutAppHeader extends StatefulWidget {
  const AboutAppHeader({super.key});
  @override
  State<AboutAppHeader> createState() => _AboutAppHeaderState();
}

class _AboutAppHeaderState extends State<AboutAppHeader> {
  late final Future<PackageInfo?> _packageInfo;
  @override
  void initState() {
    super.initState();
    _packageInfo = PackageInfo.fromPlatform()
        .then<PackageInfo?>((info) => info)
        .catchError((_) => null);
  }

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      ExcludeSemantics(
        child: SvgPic(assetName: Assets.svg.logo.path, size: 80.r),
      ),
      FutureBuilder<PackageInfo?>(
        future: _packageInfo,
        builder: (context, snapshot) {
          final PackageInfo? info = snapshot.data;
          return info == null
              ? const SizedBox.shrink()
              : AppText(
                  LocaleKeys.settingsAppVersion
                      .replaceAll('{version}', info.version)
                      .replaceAll('{build}', info.buildNumber),
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                  ),
                );
        },
      ),
    ],
  );
}
