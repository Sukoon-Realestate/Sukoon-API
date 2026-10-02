import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_calendar_content.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_request_content.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/property_review.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'helpers/collection_responses.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'collection property rental details survive caching and reach presentation',
    () {
      final json = collectionResponseData(r'/properties/[a-f0-9-]+/$');
      final property = PropertyDetailsModel.fromJson(json);
      final cached = PropertyDetailsModel.fromJson(property.toJson());
      final content = TenantPropertyDetailsContent.fromModel(cached);
      expect(content.floor, json['floor']);
      expect(content.suitableFor, json['suitable_for']);
      expect(content.smokingAllowed, json['smoking_allowed']);
      expect(
        content.photoDescriptions,
        cached.galleryImages.map((image) => image.description).toList(),
      );
      expect(content.photoLabels.length, content.imageUrls.length);
    },
  );

  test(
    'missing rental terms stay unknown while explicit ground floor and false stay visible',
    () {
      final missing = PropertyDetailsModel.fromJson({});
      expect(missing.floor, isNull);
      expect(missing.smokingAllowed, isNull);
      final explicit = PropertyDetailsModel.fromJson({
        'floor': 0,
        'smoking_allowed': false,
      });
      expect(explicit.floor, 0);
      expect(explicit.smokingAllowed, isFalse);
      expect(PropertyDetailsModel.fromJson(missing.toJson()).floor, isNull);
      expect(
        PropertyDetailsModel.fromJson(missing.toJson()).smokingAllowed,
        isNull,
      );
    },
  );

  test(
    'gallery keeps names and descriptions matched when URLs are missing or repeated',
    () {
      final property = PropertyDetailsModel.fromJson({
        'main_image': 'main.jpg',
        'images': [
          {
            'image': '',
            'name': 'Missing image',
            'description': 'Must not shift captions',
          },
          {
            'image': 'main.jpg',
            'name': 'Living room',
            'description': 'Natural light',
          },
          {
            'image': 'bedroom.jpg',
            'name': 'Bedroom',
            'description': 'Built-in storage',
          },
          {'image': 'bedroom.jpg', 'name': 'Duplicate bedroom'},
        ],
      });
      final content = TenantPropertyDetailsContent.fromModel(property);
      expect(content.imageUrls, ['main.jpg', 'bedroom.jpg']);
      expect(content.photoLabels, ['Living room', 'Bedroom']);
      expect(content.photoDescriptions, ['Natural light', 'Built-in storage']);
    },
  );

  test('an image-only gallery has no phantom main photo', () {
    final property = PropertyDetailsModel.fromJson({
      'images': [
        {
          'image': 'kitchen.jpg',
          'name': 'Kitchen',
          'description': 'Open kitchen',
        },
      ],
    });
    final content = TenantPropertyDetailsContent.fromModel(property);
    expect(content.imageUrls, ['kitchen.jpg']);
    expect(content.photoLabels, ['Kitchen']);
    expect(content.photoDescriptions, ['Open kitchen']);
    expect(const PropertyDetailsModel.initial().imageUrls, isEmpty);
    expect(const PropertyDetailsModel.initial().photoLabels, isEmpty);
  });

  test(
    'collection owner request identity, warning, subtitle and label survive caching',
    () {
      final response = collectionResponseData(
        r'/properties/owner/visits/requests/$',
      );
      for (final json
          in (response['results'] as List).cast<Map<String, dynamic>>()) {
        final request = OwnerVisitRequestContent.fromJson(json);
        final cached = OwnerVisitRequestContent.fromJson(request.toJson());
        expect(cached, request);
        expect(cached.avatar, (json['tenant'] as Map)['avatar'] ?? '');
        expect(cached.isVerified, json['is_verified_tenant']);
        expect(cached.verificationWarning, json['verification_warning']);
        expect(cached.subtitle, json['subtitle']);
        expect(cached.statusLabel, json['status_label']);
      }
    },
  );

  test(
    'owner list chat follows backend permission and verification flag takes precedence',
    () {
      final request = OwnerVisitRequestContent.fromJson({
        'tenant': {'id': 'tenant', 'is_verified': true},
        'is_verified_tenant': false,
        'actions': {'can_chat': false},
      });
      expect(request.isVerified, isFalse);
      expect(request.canChat, isFalse);
      expect(
        request
            .copyWith(actions: request.actions!.copyWith(canChat: true))
            .canChat,
        isTrue,
      );
      expect(request.copyWith(tenantId: '').canChat, isFalse);
    },
  );

  test(
    'collection calendar preserves backend labels, time, count, avatar and initial',
    () {
      final json = collectionResponseData(r'/properties/owner/calendar/$');
      final calendar = OwnerVisitCalendarContent.fromJson(json);
      final cached = OwnerVisitCalendarContent.fromJson(calendar.toJson());
      expect(cached, calendar);
      expect(cached.monthLabel, json['month_label']);
      expect(cached.selectedDateLabel, json['selected_date_label']);
      final visit = cached.visits.single;
      final raw = (json['visits'] as List).single as Map;
      expect(visit.timeFormatted, raw['time_formatted']);
      expect(visit.statusLabel, raw['status_label']);
      expect(visit.tenantInitial, (raw['tenant'] as Map)['initial']);
      expect(visit.tenant.avatar, '');
      expect(cached.visitsOn(1), 1);
      expect(cached.visitsOn(2), 0);
    },
  );

  test('calendar avatar and labels tolerate sparse older responses', () {
    final calendar = OwnerVisitCalendarContent.fromJson({
      'year': 2026,
      'month': 10,
    });
    expect(calendar.monthLabel, isEmpty);
    expect(calendar.selectedDateLabel, isEmpty);
    expect(calendar.visits, isEmpty);
    expect(
      OwnerCalendarTenantContent.fromJson({'avatar': null}).avatar,
      isEmpty,
    );
  });

  test('collection reviewer avatar survives cache serialization', () {
    final json = collectionResponseData(r'/properties/[^/]+/reviews/$');
    final raw = Map<String, dynamic>.from(
      (json['results'] as List).first as Map,
    );
    final review = PropertyReview.fromJson(raw);
    expect(review.avatarUrl, (raw['tenant'] as Map)['avatar']);
    expect(PropertyReview.fromJson(review.toJson()), review);
    expect(PropertyReview.fromJson({}).avatarUrl, isEmpty);
  });
}
