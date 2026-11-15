from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared')
p=base/'profile_menu_tile.dart'
s=p.read_text().replace('    this.subtitle,', '    this.subtitle,\n    this.subtitleLeading,')
s=s.replace('  final String? subtitle;', '  final String? subtitle;\n  final Widget? subtitleLeading;')
a=s.index('                  if (subtitle != null)\n')
b=s.index('\n                ],', a)
s=s[:a]+'''                  if (subtitle != null)
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        if (subtitleLeading != null) ...[
                          ExcludeSemantics(child: subtitleLeading!),
                          const SizedBox(width: 5),
                        ],
                        Expanded(
                          child: AppText(
                            subtitle!,
                            style: AppTextStyles.regular12.copyWith(
                              color: context.appColor(AppColors.sokoonGray),
                              fontSize: 12.sp,
                              height: 1.45,
                            ),
                          ),
                        ),
                      ],
                    ),''' +s[b:]
p.write_text(s)
p=base/'profile_verification_tile.dart'
s=p.read_text()
s=s.replace('''          ? subtitle
''', '''          ? (isVerified
              ? subtitle!.replaceFirst(RegExp(r'\\s*[✓✔]\\uFE0F?\\s*$'), '').trim()
              : subtitle)
''')
s=s.replace('''      iconColor: workspace.isOwner''', '''      subtitleLeading: isVerified
          ? Icon(
              Icons.verified_rounded,
              color: context.appColor(AppColors.sokoonTeal),
              size: 16.r,
            )
          : null,
      iconColor: workspace.isOwner''')
p.write_text(s)
