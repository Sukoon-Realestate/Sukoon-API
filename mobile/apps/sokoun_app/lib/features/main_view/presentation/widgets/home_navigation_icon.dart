import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';
import 'package:sokoun_app/shared_widgets/sokoun_count_badge.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_feedback.dart';

import '../models/home_navigation_destination.dart';

class HomeNavigationIcon extends StatelessWidget {
  const HomeNavigationIcon({
    super.key,
    required this.destination,
    required this.isSelected,
    required this.size,
  });

  final HomeNavigationDestination destination;
  final bool isSelected;
  final double size;

  @override
  Widget build(BuildContext context) {
    final Object icon = isSelected
        ? destination.selectedIcon
        : destination.icon;
    final Color color = isSelected
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonGray);
    return Stack(
      clipBehavior: Clip.none,
      children: [
        SokounSelectionFeedback(
          selected: isSelected,
          child: icon is String
              ? SvgPic(
                  assetName: icon,
                  color: context.appColor(color),
                  size: size,
                )
              : Icon(
                  icon as IconData,
                  color: context.appColor(color),
                  size: size,
                ),
        ),
        if (destination.badgeCount > 0)
          PositionedDirectional(
            top: -size * 0.32,
            end: -size * 0.5,
            child: SokounCountBadge(
              count: destination.badgeCount,
              size: size * 0.77,
            ),
          ),
      ],
    );
  }
}
