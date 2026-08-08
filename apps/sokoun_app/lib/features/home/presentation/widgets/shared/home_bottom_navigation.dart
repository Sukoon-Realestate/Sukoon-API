import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

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
        height: 70.h,
        padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
        decoration: const BoxDecoration(
          color: AppColors.white,
          border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
        ),
        child: Row(
          textDirection: TextDirection.ltr,
          children: destinations.indexed
              .map((entry) {
                final int index = entry.$1;
                final HomeNavigationDestination destination = entry.$2;

                return Expanded(
                  child: _HomeBottomNavigationItem(
                    index: index,
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

class HomeNavigationDestination {
  const HomeNavigationDestination({
    required this.icon,
    required this.selectedIcon,
    required this.label,
  });

  final IconData icon;
  final IconData selectedIcon;
  final String label;
}

class _HomeBottomNavigationItem extends StatelessWidget {
  const _HomeBottomNavigationItem({
    required this.index,
    required this.destination,
    required this.isSelected,
    required this.onPressed,
  });

  final int index;
  final HomeNavigationDestination destination;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final Color color = isSelected
        ? AppColors.sokoonTeal
        : AppColors.sokoonMuted;

    return Semantics(
      button: true,
      selected: isSelected,
      label: destination.label,
      child: InkWell(
        key: ValueKey('home-navigation-$index'),
        onTap: isSelected ? null : onPressed,
        child: ExcludeSemantics(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                isSelected ? destination.selectedIcon : destination.icon,
                color: color,
                size: 22.r,
              ),
              3.szH,
              AppText(
                destination.label,
                color: color,
                fontSize: 11.sp,
                fontWeight: FontWeight.w600,
                maxLines: 1,
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
