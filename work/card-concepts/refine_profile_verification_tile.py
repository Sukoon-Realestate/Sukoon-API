from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_verification_tile.dart')
p.write_text('''part of '../../../imports.dart';

class ProfileVerificationTile extends StatelessWidget {
  const ProfileVerificationTile({
    super.key,
    required this.workspace,
    required this.isVerified,
    this.subtitle,
  });

  final AppWorkspace workspace;
  final bool isVerified;
  final String? subtitle;

  String get _status {
    final supplied = subtitle?.trim() ?? '';
    if (supplied.isEmpty) {
      return isVerified ? LocaleKeys.verified : LocaleKeys.ownerHomeUnverified;
    }
    return isVerified
        ? supplied.replaceFirst(RegExp(r'\\s*[✓✔]\\uFE0F?\\s*$'), '').trim()
        : supplied;
  }

  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    return ProfileSurfaceCard(
      padding: EdgeInsets.zero,
      child: InkWell(
        onTap: () => Go.to(ProfileVerificationScreen(workspace: workspace)),
        borderRadius: BorderRadius.circular(14.r),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              ExcludeSemantics(
                child: Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: palette.chip,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.shield_outlined, color: palette.accent, size: 24),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppText(
                      LocaleKeys.profileIdentityVerification,
                      style: AppTextStyles.bold14.copyWith(
                        color: palette.text,
                        fontSize: 14.sp,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isVerified ? palette.chip : palette.raised,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (isVerified) ...[
                            ExcludeSemantics(child: Icon(Icons.verified_rounded, color: palette.accent, size: 16)),
                            const SizedBox(width: 5),
                          ],
                          Flexible(
                            child: AppText(
                              _status,
                              style: AppTextStyles.regular12.copyWith(
                                color: isVerified ? palette.accent : palette.muted,
                                fontSize: 12.sp,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              ExcludeSemantics(
                child: Icon(Icons.chevron_right_rounded, color: palette.muted, size: 20),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
''')
