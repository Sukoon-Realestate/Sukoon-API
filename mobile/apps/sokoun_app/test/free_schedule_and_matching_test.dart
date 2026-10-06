import 'dart:convert';
import 'package:sokoun_app/features/shared/profile/data/models/owner_profile_content.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/owner/home/data/enums/listing_quality_check.dart';
import 'package:sokoun_app/features/owner/home/data/listing_quality_data.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/property_match_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_map_viewport.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/visits/data/enums/visit_status.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/tenant_visit_content.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/visit_actions.dart';
import 'package:sokoun_app/features/tenant/visits/data/visit_calendar_data.dart';
import 'package:sokoun_app/features/tenant/visits/data/visit_schedule_rules.dart';

void main() {
  test(
    'missing acceptance rate stays unknown through caching while explicit zero stays known',
    () {
      final missing = OwnerProfileStatsContent.fromJson({});
      final zero = OwnerProfileStatsContent.fromJson({'acceptance_rate': 0});
      expect(missing.hasAcceptanceRate, isFalse);
      expect(missing.toJson(), isNot(contains('acceptance_rate')));
      expect(OwnerProfileStatsContent.fromJson(missing.toJson()), missing);
      expect(zero.hasAcceptanceRate, isTrue);
      expect(zero.displayAcceptanceRate, '0%');
      expect(OwnerProfileStatsContent.fromJson(zero.toJson()), zero);
      expect(missing.copyWith(acceptanceRate: 25).hasAcceptanceRate, isTrue);
      expect(
        OwnerProfileStatsContent.fromJson({
          'acceptance_rate': -5,
        }).hasAcceptanceRate,
        isFalse,
      );
      expect(
        OwnerProfileStatsContent.fromJson({
          'acceptance_rate': 150,
        }).hasAcceptanceRate,
        isFalse,
      );
    },
  );
  test(
    'calendar uses Egypt time and exports only exact confirmed appointments',
    () {
      const visit = TenantVisitContent(
        id: 'visit/1',
        propertyTitle: 'Apartment in Maadi',
        visitDate: '2026-06-15',
        visitTime: '14:00:00',
        day: '15 June',
        time: '2 PM',
        status: TenantVisitStatus.accepted,
        statusText: '',
      );
      final calendar = VisitCalendarData.build(
        visit,
        generatedAt: DateTime.utc(2026, 6, 1),
      )!;
      expect(calendar, contains('DTSTART:20260615T110000Z\r\n'));
      expect(calendar, contains('UID:sokoun-visit-visit%2F1@sokoun.app'));
      expect(calendar, contains('TRIGGER:-PT1H'));
      expect(calendar, isNot(contains('DTEND:')));
      expect(
        VisitCalendarData.build(
          visit.copyWith(status: TenantVisitStatus.pending),
        ),
        isNull,
      );
      expect(VisitCalendarData.build(visit.copyWith(visitDate: '')), isNull);
      expect(
        VisitCalendarData.build(visit.copyWith(visitTime: '2 PM')),
        isNull,
      );
      expect(TenantVisitContent.fromJson(visit.toJson()), visit);
    },
  );

  test('calendar escapes user text and folds Arabic by UTF8 bytes', () {
    final title =
        '${List.filled(50, 'شقة واسعة، ').join()}\nBEGIN:VEVENT;unsafe';
    final calendar = VisitCalendarData.build(
      TenantVisitContent(
        id: 'visit\r\nUID:bad',
        propertyTitle: title,
        visitDate: '2026-06-15',
        visitTime: '14:00:00',
        day: '',
        time: '',
        status: TenantVisitStatus.accepted,
        statusText: '',
      ),
    )!;
    final lines = calendar.split('\r\n');
    expect(lines.where((line) => line == 'BEGIN:VEVENT'), hasLength(1));
    expect(lines.where((line) => line.startsWith('UID:')), hasLength(1));
    expect(lines.every((line) => utf8.encode(line).length <= 75), isTrue);
    final unfolded = calendar.replaceAll('\r\n ', '');
    expect(unfolded, contains('\\nBEGIN:VEVENT\\;unsafe'));
  });

  test(
    'nonexistent local time at Egypt daylight saving change is unavailable',
    () {
      expect(VisitScheduleRules.appointment('2026-04-24', '00:30:00'), isNull);
      expect(
        VisitScheduleRules.appointment('2026-04-24', '01:30:00'),
        isNotNull,
      );
    },
  );

  test(
    'review permissions distinguish future visits and explicit server actions',
    () {
      const visit = TenantVisitContent(
        id: 'visit',
        propertyTitle: '',
        day: '',
        time: '',
        status: TenantVisitStatus.accepted,
        statusText: '',
      );
      expect(visit.canReview, isFalse);
      expect(
        visit
            .copyWith(visitDate: '2040-06-15', visitTime: '14:00:00')
            .canReview,
        isFalse,
      );
      expect(
        visit
            .copyWith(visitDate: '2020-06-15', visitTime: '14:00:00')
            .canReview,
        isTrue,
      );
      expect(
        visit.copyWith(status: TenantVisitStatus.completed).canReview,
        isTrue,
      );
      expect(
        visit.copyWith(actions: const VisitActions.initial()).canReview,
        isFalse,
      );
      expect(
        visit
            .copyWith(
              actions: const VisitActions.initial().copyWith(canReview: true),
            )
            .canReview,
        isTrue,
      );
      expect(VisitActions.fromJson({'can_chat': true}).canReview, isFalse);
    },
  );

  test('matching explanations require actual matching terms and amenities', () {
    final property = const PropertyDetailsModel.initial().copyWith(
      price: '18000',
      pricePeriod: 'monthly',
      propertyType: 'apartment',
      amenities: ['wifi'],
      bedrooms: 2,
      isVerified: true,
    );
    const preferences = PropertySearchFilters.initial(
      priceMin: '10000',
      priceMax: '20000',
      pricePeriod: 'monthly',
      propertyType: 'apartment',
      amenities: {'wifi'},
      bedrooms: '2',
      isVerified: 'true',
    );
    expect(
      PropertyMatchData.reasons(property, preferences),
      PropertyMatchReason.values.toSet(),
    );
    final changed = property.copyWith(
      pricePeriod: 'weekly',
      amenities: [],
      bedrooms: 1,
      isVerified: false,
    );
    expect(PropertyMatchData.reasons(changed, preferences), {
      PropertyMatchReason.type,
    });
    expect(
      PropertyMatchData.reasons(
        property,
        const PropertySearchFilters.initial(),
      ),
      isEmpty,
    );
  });

  test(
    'map bounds exclude absent and invalid coordinates and support the date line',
    () {
      const bounds = PropertyMapViewport(
        south: 29,
        north: 31,
        west: 30,
        east: 32,
      );
      const property = PropertyDetailsModel.initial();
      expect(
        bounds.contains(property.copyWith(latitude: '30', longitude: '31')),
        isTrue,
      );
      expect(
        bounds.contains(property.copyWith(latitude: '32', longitude: '31')),
        isFalse,
      );
      for (final value in ['', 'NaN', 'Infinity', '100']) {
        expect(
          bounds.contains(property.copyWith(latitude: value, longitude: '31')),
          isFalse,
        );
      }
      final acrossDateLine = bounds.copyWith(west: 170, east: -170);
      expect(
        acrossDateLine.contains(
          property.copyWith(latitude: '30', longitude: '-175'),
        ),
        isTrue,
      );
      expect(
        acrossDateLine.contains(
          property.copyWith(latitude: '30', longitude: '175'),
        ),
        isTrue,
      );
      expect(
        acrossDateLine.contains(
          property.copyWith(latitude: '30', longitude: '0'),
        ),
        isFalse,
      );
      expect(PropertyMapViewport.fromJson(bounds.toJson()), bounds);
    },
  );

  test(
    'quality checklist never treats unspecified deposit or empty captions as complete',
    () {
      final empty = OwnerAddPropertyFormState.initial();
      final checks = ListingQualityData.evaluate(empty);
      expect(checks.values.every((complete) => !complete), isTrue);
      final clearer = empty.copyWith(
        deposit: 'none',
        description: List.filled(50, 'a').join(),
        photoDrafts: const [
          OwnerPropertyPhotoDraft(
            existingId: '1',
            existingUrl: 'image',
            name: 'Bedroom',
          ),
        ],
      );
      expect(
        ListingQualityData.evaluate(clearer)[ListingQualityCheck.deposit],
        isTrue,
      );
      expect(
        ListingQualityData.evaluate(clearer)[ListingQualityCheck.description],
        isTrue,
      );
      expect(
        ListingQualityData.evaluate(clearer)[ListingQualityCheck.captions],
        isTrue,
      );
      expect(
        ListingQualityData.evaluate(clearer)[ListingQualityCheck.photos],
        isFalse,
      );
    },
  );
}
