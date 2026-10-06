import 'package:url_launcher/url_launcher.dart';

/// Private payment/signing links come only from authenticated APIs. No card data is collected in Flutter.
abstract final class PremiumHostedData {
  static Uri? httpsUri(String value) {
    final uri = Uri.tryParse(value);
    return uri != null &&
            uri.scheme == 'https' &&
            uri.host.isNotEmpty &&
            uri.userInfo.isEmpty
        ? uri
        : null;
  }

  static Future<bool> open(String value, {DateTime? expiresAt}) async {
    final uri = httpsUri(value);
    if (uri == null ||
        (expiresAt != null && !expiresAt.isAfter(DateTime.now()))) {
      return false;
    }
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}
