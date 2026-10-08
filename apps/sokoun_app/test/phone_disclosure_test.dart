import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_request_content.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_request_details_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/contact/data/phone_disclosure.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/tenant_visit_details_content.dart';

void main() {
  const String phone = '+20 100 123 4567';

  for (final String status in ['pending', 'rejected', 'canceled']) {
    test('$status visits do not disclose an ungranted number', () {
      final json = {
        'id': 'visit',
        'status': status,
        'tenant': {'phone_number': phone},
        'owner': {'phone_number': phone},
      };
      expect(OwnerVisitRequestContent.fromJson(json).revealedPhone, isEmpty);
      expect(
        OwnerVisitRequestDetailsContent.fromJson(json).revealedPhone,
        isEmpty,
      );
      expect(
        TenantVisitDetailsContent.fromJson(json).visit.revealedPhone,
        isEmpty,
      );
    });
  }

  for (final String status in ['accepted', 'confirmed', 'completed']) {
    test('$status visits disclose both phones and survive cache mapping', () {
      final json = {
        'id': 'visit',
        'status': status,
        'phone': '010****432',
        'owner_phone': '010****432',
        'tenant': {
          'phone_number': phone,
          'is_phone_revealed': true,
          'phone_notice': 'Phone number hidden',
        },
        'owner': {'phone_number': phone, 'is_phone_revealed': true},
      };
      final ownerList = OwnerVisitRequestContent.fromJson(json);
      final owner = OwnerVisitRequestDetailsContent.fromJson(json);
      final tenant = TenantVisitDetailsContent.fromJson(json);
      expect(ownerList.revealedPhone, phone);
      expect(owner.revealedPhone, phone);
      expect(owner.tenant.displayPhoneNotice, isEmpty);
      expect(owner.toRequestContent().revealedPhone, phone);
      expect(tenant.visit.revealedPhone, phone);
      expect(OwnerVisitRequestContent.fromJson(ownerList.toJson()), ownerList);
      expect(OwnerVisitRequestDetailsContent.fromJson(owner.toJson()), owner);
      expect(TenantVisitDetailsContent.fromJson(tenant.toJson()), tenant);
    });
  }

  test('accepted legacy visit payloads work without a disclosure flag', () {
    final json = {
      'id': 'visit',
      'status': 'confirmed',
      'tenant': {'phone_number': phone},
      'owner': {'phone_number': phone},
    };
    expect(OwnerVisitRequestDetailsContent.fromJson(json).revealedPhone, phone);
    expect(TenantVisitDetailsContent.fromJson(json).visit.revealedPhone, phone);
  });

  test('explicit denial and masked numbers never become contact numbers', () {
    expect(
      PhoneDisclosure.revealedPhone(
        phoneNumber: phone,
        isPhoneRevealed: false,
        hasAcceptedVisit: true,
      ),
      isEmpty,
    );
    for (final String value in ['', '010****432', '010••••432', 'hidden']) {
      expect(
        PhoneDisclosure.revealedPhone(
          phoneNumber: value,
          isPhoneRevealed: true,
        ),
        isEmpty,
      );
    }
  });

  test('chat requires an explicit participant grant and serializes it', () {
    final hidden = ConversationContent.fromJson({
      'id': 'conversation',
      'other_participant': {'id': 'owner', 'phone_number': phone},
    });
    expect(hidden.otherParticipant.revealedPhone, isEmpty);
    final revealed = hidden.copyWith(
      otherParticipant: hidden.otherParticipant.copyWith(isPhoneRevealed: true),
    );
    expect(revealed.otherParticipant.revealedPhone, phone);
    expect(ConversationContent.fromJson(revealed.toJson()), revealed);
  });

  test('property owner contact requires a viewer-specific server grant', () {
    final hidden = PropertyDetailsModel.fromJson({
      'id': 'property',
      'owner': {'id': 'owner', 'name': 'Owner', 'phone_number': phone},
    });
    expect(hidden.revealedOwnerPhone, isEmpty);
    final revealed = hidden.copyWith(isOwnerPhoneRevealed: true);
    expect(revealed.revealedOwnerPhone, phone);
    expect(PropertyDetailsModel.fromJson(revealed.toJson()), revealed);
    expect(TenantPropertyDetailsContent.fromModel(revealed).ownerPhone, phone);
  });
}
