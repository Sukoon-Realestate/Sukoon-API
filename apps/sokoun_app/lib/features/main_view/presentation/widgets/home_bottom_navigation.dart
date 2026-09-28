import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';

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
    this.badgeCount = 0,
  });

  final Object icon;
  final Object selectedIcon;
  final String label;
  final int badgeCount;

  HomeNavigationDestination copyWith({int? badgeCount}) {
    return HomeNavigationDestination(
      icon: icon,
      selectedIcon: selectedIcon,
      label: label,
      badgeCount: badgeCount ?? this.badgeCount,
    );
  }
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
      value: destination.badgeCount > 0 ? '${destination.badgeCount}' : null,
      child: InkWell(
        onTap: isSelected ? null : onPressed,
        child: ExcludeSemantics(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Stack(
                clipBehavior: Clip.none,
                children: [
                  _buildIcon(color),
                  if (destination.badgeCount > 0)
                    PositionedDirectional(
                      top: -7.r,
                      end: -11.r,
                      child: Container(
                        constraints: BoxConstraints(minWidth: 17.r),
                        height: 17.r,
                        alignment: Alignment.center,
                        padding: EdgeInsets.symmetric(horizontal: 4.w),
                        decoration: BoxDecoration(
                          color: AppColors.red,
                          borderRadius: BorderRadius.circular(999.r),
                          border: Border.all(color: AppColors.white),
                        ),
                        child: AppText(
                          destination.badgeCount > 99
                              ? '99+'
                              : '${destination.badgeCount}',
                          color: AppColors.white,
                          fontSize: 9.sp,
                          fontWeight: FontWeight.w800,
                          maxLines: 1,
                        ),
                      ),
                    ),
                ],
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

  Widget _buildIcon(Color color) {
    final Object icon = isSelected
        ? destination.selectedIcon
        : destination.icon;

    if (icon is String) {
      return SvgPic(assetName: icon, color: color, size: 22.r);
    }

    return Icon(icon as IconData, color: color, size: 22.r);
  }
}
