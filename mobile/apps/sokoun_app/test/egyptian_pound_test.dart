import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_revenue_content.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

void main() {
  group('Egyptian pound amounts', () {
    for (final (value, expected) in <(Object, String)>[
      (0, '0'),
      (6500, '6,500'),
      ('6,500.75', '6,500.75'),
      (' 6500.50 ', '6,500.5'),
      ('٦٬٥٠٠٫٧٥', '6,500.75'),
      ('۶۵۰۰.۷۵', '6,500.75'),
      (0.05, '0.05'),
      (-125.75, '-125.75'),
      (1250000, '1,250,000'),
    ]) {
      test('formats $value without dropping piastres', () {
        expect(EgyptianPound.formatAmount(value), expected);
      });
    }

    test('invalid amounts are not presented as zero or foreign money', () {
      for (final value in [
        null,
        '',
        'not a price',
        '125 SAR',
        '125 ر.س',
        double.nan,
        double.infinity,
      ]) {
        expect(EgyptianPound.parseAmount(value), isNull);
        expect(EgyptianPound.formatAmount(value), '—');
      }
    });
  });

  test('property amounts retain piastres through mapping and caching', () {
    final owner = OwnerPropertyContent.fromJson({
      'id': 'property',
      'price': '6,500.75',
      'price_period': 'monthly',
    });
    expect(owner.monthlyPrice, 6500.75);
    expect(OwnerPropertyContent.fromJson(owner.toJson()), owner);
    expect(owner.copyWith(monthlyPrice: 6500.5).monthlyPrice, 6500.5);

    final tenant = PropertyDetailsModel.fromJson({
      'price': '6,500.75',
      'price_period': 'monthly',
    });
    expect(tenant.formattedPrice, '6,500.75');
    expect(PropertyDetailsModel.fromJson(tenant.toJson()), tenant);
  });

  test('revenue retains raw metadata but formats canonical amounts', () {
    final revenue = OwnerRevenueContent.fromJson({
      'total_this_month': '36,000.75',
      'formatted_total': '36,000 SAR',
      'currency': 'SAR',
      'properties': [
        {
          'id': 'property',
          'amount': '6,500.5',
          'formatted_amount': '6,500 ر.س',
          'currency': 'ر.س',
        },
      ],
      'recent_transactions': [
        {
          'id': 'debit',
          'amount': '-125.75',
          'formatted_amount': '-125 USD',
          'currency': 'USD',
          'is_credit': false,
        },
      ],
    });
    expect(revenue.totalThisMonth, 36000.75);
    expect(revenue.totalLabel, '36,000.75');
    expect(revenue.properties.single.amountLabel, '6,500.5');
    expect(revenue.transactions.single.amountLabel, '125.75');
    expect(revenue.transactions.single.isCredit, isFalse);
    expect(revenue.currency, 'SAR');
    expect(revenue.formattedTotal, '36,000 SAR');
    expect(OwnerRevenueContent.fromJson(revenue.toJson()), revenue);
  });

  test('all app currency translations specify Egyptian pounds', () {
    Map<String, dynamic> translations(String locale) =>
        jsonDecode(
              File(
                '../../packages/core/assets/translations/$locale.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;
    final ar = translations('ar');
    final en = translations('en');
    expect(en['egyptian_pound_short'], EgyptianPound.code);
    expect(ar['egyptian_pound_short'], 'ج.م');
    for (final key in [
      'favorites_currency_short',
      'owner_add_property_currency',
      'owner_add_property_monthly_price',
      'owner_properties_price_unit',
      'owner_revenue_currency',
      'tenant_property_details_daily_price_unit',
      'tenant_property_details_weekly_price_unit',
      'tenant_property_details_monthly_price_unit',
      'tenant_property_details_yearly_price_unit',
    ]) {
      expect(en[key], contains('EGP'), reason: key);
      expect(ar[key], contains('ج.م'), reason: key);
    }
    expect(en['owner_add_property_monthly_price'], contains('{price}'));
  });
}
