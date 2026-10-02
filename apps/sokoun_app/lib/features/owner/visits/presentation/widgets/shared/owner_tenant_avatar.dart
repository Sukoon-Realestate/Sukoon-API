import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';

class OwnerTenantAvatar extends StatelessWidget {
  const OwnerTenantAvatar({
    super.key,
    required this.name,
    this.avatarUrl = '',
    this.initial = '',
    this.size = 40,
  });

  final String name;
  final String avatarUrl;
  final String initial;
  final double size;

  @override
  Widget build(BuildContext context) {
    final String label = initial.trim().isNotEmpty
        ? initial
        : name.trim().isEmpty
        ? ''
        : name.trim().characters.first;
    final Widget fallback = Center(
      child: AppText(
        label,
        style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonTeal),
      ),
    );
    return ExcludeSemantics(
      child: Container(
        width: size.r,
        height: size.r,
        clipBehavior: Clip.antiAlias,
        decoration: const BoxDecoration(
          color: AppColors.tealAlpha13,
          shape: BoxShape.circle,
        ),
        child: avatarUrl.trim().isEmpty
            ? fallback
            : CachedImage(
                url: avatarUrl,
                width: size.r,
                height: size.r,
                fit: BoxFit.cover,
                boxShape: BoxShape.circle,
                bgColor: AppColors.tealAlpha13,
                placeHolder: fallback,
              ),
      ),
    );
  }
}
