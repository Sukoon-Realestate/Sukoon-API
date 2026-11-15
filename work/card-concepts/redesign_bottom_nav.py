from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/main_view/presentation/widgets/home_bottom_navigation.dart'
s=p.read_text().replace('fontSize: 10.sp,','fontSize: 11,').replace('double width = 48.w;','double width = 56;')
s=s.replace('''    return DecoratedBox(
      decoration: BoxDecoration(
        color: palette.surface,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: SafeArea(
        top: false,''','''    return SafeArea(
      top: false,
      minimum: const EdgeInsets.fromLTRB(12, 8, 12, 8),
      child: Material(
        color: palette.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: palette.line),
        ),
        clipBehavior: Clip.antiAlias,''')
s=s.replace('constraints: BoxConstraints(minHeight: 64.h),','constraints: const BoxConstraints(minHeight: 76),')
s=s.replace('padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 4.h),','padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 8),')
p.write_text(s)
p=root/'lib/features/main_view/presentation/widgets/home_navigation_item.dart'
s=p.read_text().replace("import 'package:melos_core/config/res/config_imports.dart';\n",'')
s=s.replace('/// Shared accessible destinations for the flat bottom bar and desktop rail.','/// Shared accessible destinations for the bottom dock and desktop rail.')
s=s.replace('minimumSize: Size(48.w, 60.h),','minimumSize: const Size(48, 64),')
s=s.replace('alignment: Alignment.topCenter,','alignment: Alignment.center,')
s=s.replace('''            if (selected) return;
            SokounFeedback.selectionChanged(context);''','''            if (!selected) SokounFeedback.selectionChanged(context);''')
s=s.replace('spacing: 6.h,','spacing: 4,')
a=s.index('                  padding: EdgeInsets.symmetric(')
b=s.index('                  child: HomeNavigationIcon(',a)
s=s[:a]+'''                  padding: EdgeInsets.symmetric(
                    horizontal: rail ? 12.w : 2,
                    vertical: rail ? 8.h : 2,
                  ),
                  decoration: BoxDecoration(
                    color: selected ? palette.chip : Colors.transparent,
                    borderRadius: BorderRadius.circular(16),
                  ),
'''+s[b:]
s=s.replace('size: rail ? 24.r : 22.r,','size: rail ? 24.r : 24,')
s=s.replace('fontSize: rail ? 12.sp : 10.sp,','fontSize: rail ? 12.sp : 11,').replace('height: 1.4,','height: 1.3,').replace('color: selected ? palette.accent : palette.muted,','color: selected ? palette.text : palette.muted,')
p.write_text(s)
p=root/'lib/features/main_view/presentation/widgets/home_navigation_icon.dart'
s=p.read_text().replace("import 'package:melos_core/config/res/config_imports.dart';", "import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';")
s=s.replace('''    final Color color = isSelected
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonGray);''','''    final palette = SokounPalette.of(context);
    final Color color = isSelected ? palette.text : palette.muted;''')
s=s.replace('''    return Stack(
      clipBehavior: Clip.none,
      children: [
        SokounSelectionFeedback(''','''    return SizedBox(
      width: size + 24,
      height: size + 14,
      child: Stack(
      clipBehavior: Clip.none,
      children: [
        Align(
          alignment: Alignment.bottomCenter,
          child: SokounSelectionFeedback(''')
s=s.replace('''        ),
        if (destination.badgeCount > 0)''','''        ),
        ),
        if (destination.badgeCount > 0)''',1)
s=s.replace('''            top: -(MediaQuery.textScalerOf(context).scale(9) * 1.2 + 6) + 6,
            end: -size * 0.5,''','''            top: 0,
            end: 0,''')
s=s.replace('''      ],
    );''','''      ],
      ),
    );''')
p.write_text(s)
p=root/'test/liquid_glass_navigation_test.dart'
s=p.read_text().replace('''          await tester.tapAt(tester.getCenter(second));
          await tester.pumpAndSettle();
          expect(calls, [1]);''','''          await tester.tapAt(tester.getCenter(second));
          await tester.pumpAndSettle();
          expect(calls, [1, 1]);''')
p.write_text(s)
