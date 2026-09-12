part of '../../../imports.dart';

class ProfileAvatar extends StatelessWidget {
  const ProfileAvatar({
    super.key,
    required this.name,
    required this.accentColor,
    required this.backgroundColor,
    this.avatarUrl,
    this.imageFile,
    this.size = 64,
    this.useInitial = false,
    this.badgeIcon,
    this.onBadgePressed,
  });

  final String name;
  final Color accentColor;
  final Color backgroundColor;
  final String? avatarUrl;
  final File? imageFile;
  final double size;
  final bool useInitial;
  final IconData? badgeIcon;
  final VoidCallback? onBadgePressed;

  String get _initial {
    final String normalizedName = name.trim();
    if (normalizedName.isEmpty) {
      return '?';
    }
    return normalizedName.characters.first;
  }

  @override
  Widget build(BuildContext context) {
    final double avatarSize = size.r;
    final double badgeSize = size <= 64 ? 24.r : 28.r;

    return SizedBox(
      width: avatarSize + 4.w,
      height: avatarSize + 4.h,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            width: avatarSize,
            height: avatarSize,
            decoration: BoxDecoration(
              color: backgroundColor,
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: imageFile != null
                ? ClipOval(
                    child: Image.file(
                      imageFile!,
                      width: avatarSize,
                      height: avatarSize,
                      fit: BoxFit.cover,
                    ),
                  )
                : avatarUrl?.trim().isNotEmpty == true
                ? ClipOval(
                    child: Image.network(
                      avatarUrl!,
                      width: avatarSize,
                      height: avatarSize,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => _fallbackAvatar(),
                    ),
                  )
                : _fallbackAvatar(),
          ),
          if (badgeIcon != null)
            PositionedDirectional(
              end: -2.w,
              bottom: -2.h,
              child: Material(
                color: accentColor,
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: onBadgePressed,
                  customBorder: const CircleBorder(),
                  child: Container(
                    width: badgeSize,
                    height: badgeSize,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.white, width: 2.r),
                    ),
                    child: Icon(
                      badgeIcon,
                      color: AppColors.white,
                      size: (badgeSize * .48),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _fallbackAvatar() {
    if (useInitial) {
      return AppText(
        _initial,
        color: AppColors.white,
        fontSize: (size * .36).sp,
        fontWeight: FontWeight.w900,
      );
    }
    return Icon(
      Icons.person_outline_rounded,
      color: accentColor,
      size: (size * .47).r,
    );
  }
}
