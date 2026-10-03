part of '../../../imports.dart';

class ProfileMenuItem {
  const ProfileMenuItem({
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

class ProfileMenuSection extends StatelessWidget {
  const ProfileMenuSection({
    super.key,
    required this.title,
    required this.items,
  });

  final String title;
  final List<ProfileMenuItem> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: 7.h,
      children: [
        AppText(
          title,
          style: AppTextStyles.bold12.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
        ),
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: Column(
            children: items.indexed
                .map((entry) {
                  final int index = entry.$1;
                  final ProfileMenuItem item = entry.$2;
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
