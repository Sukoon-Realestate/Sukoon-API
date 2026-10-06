import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'models/lease_draft_body.dart';

abstract final class LeaseRules {
  static DateTime? date(String value) {
    if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(value)) return null;
    final result = DateTime.tryParse(value);
    return result != null && result.toIso8601String().substring(0, 10) == value
        ? result
        : null;
  }

  static PremiumMoney money(String value) {
    if (!RegExp(r'^\d+(?:\.\d{1,2})?$').hasMatch(value.trim())) {
      return const PremiumMoney.initial();
    }
    final parts = value.trim().split('.');
    final major = int.tryParse(parts.first);
    if (major == null || major > 999999999) return const PremiumMoney.initial();
    return PremiumMoney(
      amountMinor:
          major * 100 +
          (parts.length == 2 ? int.parse(parts.last.padRight(2, '0')) : 0),
      currency: 'EGP',
    );
  }

  static bool valid(LeaseDraftBody body) {
    final start = date(body.startDate), end = date(body.endDate);
    return body.propertyId.isNotEmpty &&
        body.tenantId.trim().isNotEmpty &&
        body.templateId.isNotEmpty &&
        body.templateVersion.isNotEmpty &&
        start != null &&
        end != null &&
        end.isAfter(start) &&
        body.rent.isKnown &&
        body.rent.amountMinor! > 0 &&
        body.rent.currency == 'EGP' &&
        body.rent.exponent == 2 &&
        body.requestKey.isNotEmpty;
  }
}
