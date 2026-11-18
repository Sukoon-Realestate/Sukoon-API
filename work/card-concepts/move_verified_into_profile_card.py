from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_header_card.dart')
s=p.read_text()
old='''                ColoredBox(
                  color: SokounPalette.of(context).hero,
                  child: SokounWordmark(
                    size: 52.r,
                    color: SokounPalette.of(context).onHero,
                  ),
                ),'''
new='''                Row(
                  children: [
                    ColoredBox(
                      color: SokounPalette.of(context).hero,
                      child: SokounWordmark(
                        size: 52.r,
                        color: SokounPalette.of(context).onHero,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Spacer(),
                    Flexible(
                      child: ProfileVerifiedBadge(text: badgeText, isVerified: isVerified),
                    ),
                  ],
                ),'''
assert old in s
s=s.replace(old,new,1)
old='''        Wrap(
          spacing: 8.w,
          runSpacing: 8.h,
          children: [
            ProfileVerifiedBadge(text: badgeText, isVerified: isVerified),
          ],
        ),
'''
assert old in s
p.write_text(s.replace(old,'',1))
