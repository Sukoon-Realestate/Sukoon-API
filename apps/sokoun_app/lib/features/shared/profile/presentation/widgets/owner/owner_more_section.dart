part of '../../../imports.dart';

class OwnerMoreItem {
  const OwnerMoreItem({
    required this.icon,
    required this.label,
    required this.color,
    required this.backgroundColor,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final Color backgroundColor;
  final VoidCallback? onTap;
}

class OwnerMoreSection extends StatelessWidget {
  const OwnerMoreSection({super.key, required this.title, required this.items});

  final String title;
  final List<OwnerMoreItem> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppText(
          title,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w700,
        ),
        7.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: Column(
            children: items.indexed
                .map((entry) {
                  final int index = entry.$1;
                  final OwnerMoreItem item = entry.$2;
                  return ProfileMenuTile(
                    icon: item.icon,
                    label: item.label,
                    iconColor: item.color,
                    iconBackgroundColor: item.backgroundColor,
                    onTap: item.onTap,
                    showDivider: index < items.length - 1,
                  );
                })
                .toList(growable: false),
          ),
        ),
      ],
    );
  }
}
