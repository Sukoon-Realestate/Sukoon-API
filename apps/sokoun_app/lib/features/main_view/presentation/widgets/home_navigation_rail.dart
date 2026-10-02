import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import '../models/home_navigation_destination.dart';
import 'home_navigation_icon.dart';

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
            const ExcludeSemantics(child: AppLogoWidget()),
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
                          spacing: 8,
                          children: [
                            HomeNavigationIcon(
                              destination: destinations[i],
                              isSelected: i == currentIndex,
                              size: 24,
                            ),
                            AppText(
                              destinations[i].label,
                              textAlign: TextAlign.center,
                              style: AppTextStyles.regular12.copyWith(
                                fontSize: 12,
                                color: i == currentIndex
                                    ? AppColors.sokoonTeal
                                    : AppColors.sokoonGray,
                                fontWeight: i == currentIndex
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                height: 1.45,
                              ),
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
}
