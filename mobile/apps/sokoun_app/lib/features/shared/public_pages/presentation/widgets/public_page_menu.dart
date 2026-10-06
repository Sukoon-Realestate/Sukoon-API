import 'package:flutter/material.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import '../../data/enums/public_page.dart';
import '../screens/public_page_screen.dart';
import '../public_page_labels.dart';

class PublicPageMenu extends StatelessWidget {
  const PublicPageMenu({super.key});
  @override
  Widget build(BuildContext context) => Material(
    type: MaterialType.transparency,
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final page in PublicPage.values)
          ListTile(
            leading: Icon(switch (page) {
              PublicPage.aboutUs => Icons.info_outline,
              PublicPage.privacy => Icons.privacy_tip_outlined,
              PublicPage.terms => Icons.description_outlined,
            }),
            title: AppText(
              publicPageTitle(page),
              style: AppTextStyles.regular14,
            ),
            onTap: () => Go.to(PublicPageScreen(page: page)),
          ),
      ],
    ),
  );
}
