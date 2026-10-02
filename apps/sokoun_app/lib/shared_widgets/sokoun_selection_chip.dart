import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import 'sokoun_motion.dart';

class SokounSelectionChip extends StatelessWidget {
  const SokounSelectionChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onPressed,
    this.showCheck = true,
  });

  final String label;
  final bool selected;
  final VoidCallback? onPressed;
  final bool showCheck;

  @override
  Widget build(BuildContext context) {
    final duration = SokounMotion.duration(context, milliseconds: 180);
    return Semantics(
      button: true,
      selected: selected,
      enabled: onPressed != null,
      child: Material(
        color: AppColors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(999),
          child: AnimatedContainer(
            duration: duration,
            curve: SokounMotion.curve,
            constraints: const BoxConstraints(minHeight: 48),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: selected ? AppColors.tealAlpha07 : AppColors.white,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(
                color: selected ? AppColors.sokoonTeal : AppColors.grayPale,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (showCheck)
                  TweenAnimationBuilder<double>(
                    tween: Tween<double>(end: selected ? 1 : 0),
                    duration: duration,
                    curve: SokounMotion.curve,
                    builder: (context, value, child) => ClipRect(
                      child: Align(
                        alignment: AlignmentDirectional.centerStart,
                        widthFactor: value,
                        child: Opacity(opacity: value, child: child),
                      ),
                    ),
                    child: const ExcludeSemantics(
                      child: SizedBox(
                        width: 20,
                        child: Icon(
                          Icons.check_rounded,
                          size: 16,
                          color: AppColors.sokoonTeal,
                        ),
                      ),
                    ),
                  ),
                Flexible(
                  child: AppText(
                    label,
                    style: AppTextStyles.bold12.copyWith(
                      color: selected
                          ? AppColors.sokoonTeal
                          : AppColors.sokoonNavy,
                      height: 1.45,
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
