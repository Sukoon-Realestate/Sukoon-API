import 'package:melos_core/core/network/api_endpoints.dart';

enum PublicPage {
  aboutUs(ApiConstants.aboutUs),
  privacy(ApiConstants.privacyPolicy),
  terms(ApiConstants.terms);

  const PublicPage(this.endpoint);
  final String endpoint;
}
