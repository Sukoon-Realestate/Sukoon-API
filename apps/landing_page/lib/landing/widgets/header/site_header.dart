import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'header_actions.dart';
import 'language_button.dart';
import 'header_desktop_navigation.dart';
import 'header_navigation_menu.dart';

class SiteHeader extends StatelessWidget {
  const SiteHeader({
    required this.scrolled,
    required this.onNavigate,
    super.key,
  });

  final bool scrolled;
  final ValueChanged<String> onNavigate;

  static List<(String, String)> get _navItems => [
    (LocaleKeys.landingNavHome, 'hero'),
    (LocaleKeys.landingNavTenant, 'tenant'),
    (LocaleKeys.landingNavOwner, 'owner'),
    (LocaleKeys.landingNavTrust, 'trust'),
    (LocaleKeys.landingNavHow, 'how'),
    (LocaleKeys.landingNavFaq, 'faq'),
    (LocaleKeys.landingStartNow, 'download'),
  ];

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final showDesktopNav = width >= 1280;
    final showActions = width >= LandingBreakpoints.mobile;

    return AnimatedContainer(
      duration: Duration(
        milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 250,
      ),
      height: 68,
      decoration: BoxDecoration(
        color: scrolled
            ? LandingColors.background.withValues(alpha: 0.97)
            : LandingColors.background,
        border: Border(
          bottom: BorderSide(
            color: scrolled ? LandingColors.border : Colors.transparent,
          ),
        ),
        boxShadow: scrolled
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.025),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ]
            : null,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: SiteContent(
          child: Row(
            children: [
              InkWell(
                onTap: () => onNavigate('hero'),
                borderRadius: BorderRadius.circular(12),
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 6),
                  child: SokoonLogo(),
                ),
              ),
              const SizedBox(width: 20),
              if (showDesktopNav)
                HeaderDesktopNavigation(
                  items: _navItems.take(6).toList(),
                  onNavigate: onNavigate,
                )
              else
                const Spacer(),
              const SizedBox(width: 20),
              const LanguageButton(),
              if (showActions)
                HeaderActions(
                  showMenuSpacing: !showDesktopNav,
                  onNavigate: onNavigate,
                ),
              if (!showDesktopNav)
                HeaderNavigationMenu(items: _navItems, onNavigate: onNavigate),
            ],
          ),
        ),
      ),
    );
  }
}
