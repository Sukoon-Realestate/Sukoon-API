import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import '../models/home_navigation_destination.dart';
import 'home_navigation_icon.dart';

class HomeBottomNavigation extends StatelessWidget {
  const HomeBottomNavigation({
    super.key,
    required this.destinations,
    required this.currentIndex,
    required this.onDestinationSelected,
  });

  final List<HomeNavigationDestination> destinations;
  final int currentIndex;
  final ValueChanged<int> onDestinationSelected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        constraints: BoxConstraints(minHeight: 76.h),
        padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
        decoration: const BoxDecoration(
          color: AppColors.white,
          border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
        ),
        child: Row(
          children: destinations.indexed
              .map((entry) {
                final int index = entry.$1;
                final HomeNavigationDestination destination = entry.$2;

                return Expanded(
                  child: _HomeBottomNavigationItem(
                    destination: destination,
                    isSelected: currentIndex == index,
                    onPressed: () => onDestinationSelected(index),
                  ),
                );
              })
              .toList(growable: false),
        ),
      ),
    );
  }
}

class _HomeBottomNavigationItem extends StatelessWidget {
  const _HomeBottomNavigationItem({
    required this.destination,
    required this.isSelected,
    required this.onPressed,
  });

  final HomeNavigationDestination destination;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final Color color = isSelected
        ? AppColors.sokoonTeal
        : AppColors.sokoonGray;

    return Semantics(
      button: true,
      selected: isSelected,
      label: destination.label,
      value: destination.badgeCount > 0 ? '${destination.badgeCount}' : null,
      child: InkWell(
        onTap: isSelected ? null : onPressed,
        child: ExcludeSemantics(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            spacing: 3.h,
            children: [
              AnimatedContainer(
                duration: SokounMotion.duration(context),
                curve: SokounMotion.curve,
                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: isSelected
                      ? AppColors.mintLight
                      : AppColors.transparent,
                  borderRadius: BorderRadius.circular(16.r),
                ),
                child: HomeNavigationIcon(
                  destination: destination,
                  isSelected: isSelected,
                  size: 22.r,
                ),
              ),
              AppText(
                destination.label,
                style: AppTextStyles.semiBold.copyWith(
                  color: color,
                  fontSize: 11.sp,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
