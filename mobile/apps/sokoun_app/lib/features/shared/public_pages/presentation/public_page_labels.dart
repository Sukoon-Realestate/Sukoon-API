import 'package:melos_core/config/language/locale_keys.g.dart';
import '../data/enums/public_page.dart';

String publicPageTitle(PublicPage page) => switch (page) {
  PublicPage.aboutUs => LocaleKeys.publicAboutUs,
  PublicPage.privacy => LocaleKeys.publicPrivacyPolicy,
  PublicPage.terms => LocaleKeys.publicTerms,
};
