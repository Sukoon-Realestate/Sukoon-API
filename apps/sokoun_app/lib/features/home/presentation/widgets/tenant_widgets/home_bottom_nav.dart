import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class HomeBottomNav extends StatelessWidget {
  const HomeBottomNav({super.key, required this.items});

  final List<HomeBottomNavItemData> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 70.h,
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: items.map((item) {
          return Expanded(child: _HomeBottomNavItem(item: item));
        }).toList(),
      ),
    );
  }
}

class HomeBottomNavItemData {
  const HomeBottomNavItemData({
    required this.icon,
    required this.label,
    this.isActive = false,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback? onTap;
}

class _HomeBottomNavItem extends StatelessWidget {
  const _HomeBottomNavItem({required this.item});

  final HomeBottomNavItemData item;

  @override
  Widget build(BuildContext context) {
    final color = item.isActive ? AppColors.sokoonTeal : AppColors.sokoonMuted;

    return Semantics(
      button: item.onTap != null,
      selected: item.isActive,
      label: item.label,
      child: GestureDetector(
        onTap: item.onTap,
        behavior: HitTestBehavior.opaque,
        child: ExcludeSemantics(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(item.icon, color: color, size: 22.r),
              3.szH,
              AppText(
                item.label,
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
