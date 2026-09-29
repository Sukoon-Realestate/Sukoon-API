import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import 'home_bottom_navigation.dart';

class HomeNavigationRail extends StatelessWidget {
  const HomeNavigationRail({
    super.key,
    required this.destinations,
    required this.currentIndex,
    required this.onDestinationSelected,
  });

  final List<HomeNavigationDestination> destinations;
  final int currentIndex;
  final ValueChanged<int> onDestinationSelected;

  @override
  Widget build(BuildContext context) => Material(
    color: AppColors.white,
    child: SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 24),
        child: Column(
          children: [
            const ExcludeSemantics(
              child: AppLogoWidget(size: 36, color: AppColors.sokoonTeal),
            ),
            const SizedBox(height: 32),
            for (int i = 0; i < destinations.length; i++)
              Semantics(
                selected: i == currentIndex,
                button: true,
                label: destinations[i].label,
                value: destinations[i].badgeCount > 0
                    ? '${destinations[i].badgeCount}'
                    : null,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(16),
                    onTap: () => onDestinationSelected(i),
                    child: AnimatedContainer(
                      duration: SokounMotion.duration(context),
                      curve: SokounMotion.curve,
                      padding: const EdgeInsets.symmetric(
                        vertical: 12,
                        horizontal: 4,
                      ),
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: i == currentIndex
                            ? AppColors.mintLight
                            : AppColors.transparent,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ExcludeSemantics(
                        child: Column(
                          children: [
                            Badge(
                              isLabelVisible: destinations[i].badgeCount > 0,
                              label: Text(
                                destinations[i].badgeCount > 99
                                    ? '99+'
                                    : '${destinations[i].badgeCount}',
                              ),
                              child: _icon(i),
                            ),
                            const SizedBox(height: 8),
                            AppText(
                              destinations[i].label,
                              textAlign: TextAlign.center,
                              fontSize: 12,
                              color: i == currentIndex
                                  ? AppColors.sokoonTeal
                                  : AppColors.sokoonGray,
                              fontWeight: i == currentIndex
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    ),
  );

  Widget _icon(int index) {
    final Object icon = index == currentIndex
        ? destinations[index].selectedIcon
        : destinations[index].icon;
    final Color color = index == currentIndex
        ? AppColors.sokoonTeal
        : AppColors.sokoonGray;
    return icon is String
        ? SvgPic(assetName: icon, size: 24, color: color)
        : Icon(icon as IconData, size: 24, color: color);
  }
}
