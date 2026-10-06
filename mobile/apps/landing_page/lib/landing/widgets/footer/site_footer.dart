import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'footer_brand.dart';
import 'footer_column.dart';

class SiteFooter extends StatelessWidget {
  const SiteFooter({required this.onNavigate, super.key});

  final ValueChanged<String> onNavigate;

  static List<(String, List<(String, String)>)> get _columns => [
    (
      LocaleKeys.landingFooterPlatform,
      [
        (LocaleKeys.landingNavHome, 'hero'),
        (LocaleKeys.landingNavTenant, 'tenant'),
        (LocaleKeys.landingNavOwner, 'owner'),
        (LocaleKeys.landingNavHow, 'how'),
      ],
    ),
    (
      LocaleKeys.landingFooterHelp,
      [
        (LocaleKeys.landingNavFaq, 'faq'),
        (LocaleKeys.landingNavTrust, 'trust'),
      ],
    ),
    (
      LocaleKeys.landingAppTag,
      [
        (LocaleKeys.landingPreviewAction, 'app'),
        (LocaleKeys.landingStartNow, 'download'),
      ],
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: LandingColors.navy,
      padding: const EdgeInsets.fromLTRB(24, 56, 24, 28),
      child: SiteContent(
        child: Column(
          children: [
            ResponsiveGrid(
              desktopColumns: 4,
              tabletColumns: 2,
              minItemWidth: 220,
              spacing: 40,
              runSpacing: 38,
              children: [
                const FooterBrand(),
                ..._columns.map(
                  (column) => FooterColumn(
                    title: column.$1,
                    links: column.$2,
                    onNavigate: onNavigate,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 48),
            Divider(color: Colors.white.withValues(alpha: 0.1), height: 1),
            const SizedBox(height: 24),
            Wrap(
              alignment: WrapAlignment.spaceBetween,
              runAlignment: WrapAlignment.center,
              spacing: 24,
              runSpacing: 8,
              children: [
                Text(
                  '${String.fromCharCode(0x00A9)} '
                  '${LocaleKeys.landingFooterCopyright}',
                  style: const TextStyle(
                    color: Color(0x66FFFFFF),
                    fontSize: 13,
                  ),
                ),
                Text(
                  LocaleKeys.landingFooterCountry,
                  style: const TextStyle(
                    color: Color(0x4DFFFFFF),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
