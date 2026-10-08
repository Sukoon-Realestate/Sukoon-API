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

  for (final String status in [
    'pending',
    'rejected',
    'canceled',
    'accepted',
    'confirmed',
    'completed',
  ]) {
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

  for (final String status in [
    'pending',
    'rejected',
    'canceled',
    'accepted',
    'confirmed',
    'completed',
  ]) {
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

  test('an explicit denial overrides accepted status in every visit read', () {
    final json = {
      'id': 'visit',
      'status': 'confirmed',
      'tenant': {'phone_number': phone, 'is_phone_revealed': false},
      'owner': {'phone_number': phone, 'is_phone_revealed': false},
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

  test('explicit denial and masked numbers never become contact numbers', () {
    expect(
      PhoneDisclosure.revealedPhone(phoneNumber: phone, isPhoneRevealed: false),
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

  test(
    'an authorized null phone clears stale flattened numbers and notices',
    () {
      final json = {
        'id': 'visit',
        'status': 'canceled',
        'phone': phone,
        'owner_phone': phone,
        'tenant': {
          'phone_number': null,
          'is_phone_revealed': true,
          'masked_phone_number': '010****432',
          'phone_notice': 'Phone number hidden',
        },
        'owner': {
          'id': 'owner',
          'phone_number': null,
          'is_phone_revealed': true,
        },
        'actions': {'can_chat': true},
      };
      final ownerList = OwnerVisitRequestContent.fromJson(json);
      final owner = OwnerVisitRequestDetailsContent.fromJson(json);
      final tenant = TenantVisitDetailsContent.fromJson(json);
      expect(ownerList.phone, isEmpty);
      expect(ownerList.isPhoneRevealed, isTrue);
      expect(owner.tenant.displayPhone, isEmpty);
      expect(owner.tenant.displayPhoneNotice, isEmpty);
      expect(tenant.visit.ownerPhone, isEmpty);
      expect(tenant.visit.isPhoneRevealed, isTrue);
      expect(tenant.visit.canChat, isTrue);
      expect(TenantVisitDetailsContent.fromJson(tenant.toJson()), tenant);
    },
  );

  test('a nested unknown permission cannot reuse a stale flattened grant', () {
    final json = {
      'status': 'confirmed',
      'is_phone_revealed': true,
      'tenant': {'phone_number': phone, 'is_phone_revealed': null},
      'owner': {'phone_number': phone, 'is_phone_revealed': null},
    };
    expect(OwnerVisitRequestContent.fromJson(json).revealedPhone, isEmpty);
    expect(
      TenantVisitDetailsContent.fromJson(json).visit.revealedPhone,
      isEmpty,
    );
  });

  test(
    'authorized empty contact remains granted in conversation snapshots',
    () {
      final conversation = ConversationContent.fromJson({
        'id': 'conversation',
        'other_participant': {
          'id': 'owner',
          'phone_number': null,
          'is_phone_revealed': true,
          'masked_phone_number': '010****432',
          'phone_notice': 'Phone number hidden',
          'can_send': true,
        },
      });
      expect(conversation.otherParticipant.isPhoneRevealed, isTrue);
      expect(conversation.otherParticipant.revealedPhone, isEmpty);
      expect(conversation.canSend, isTrue);
      expect(ConversationContent.fromJson(conversation.toJson()), conversation);
    },
  );

  test(
    'property presentation preserves authorized but unavailable contacts',
    () {
      final model = PropertyDetailsModel.fromJson({
        'id': 'property',
        'owner_phone': phone,
        'owner': {
          'id': 'owner',
          'phone_number': null,
          'is_phone_revealed': true,
        },
      });
      expect(model.ownerPhone, isEmpty);
      expect(model.isOwnerPhoneRevealed, isTrue);
      final content = TenantPropertyDetailsContent.fromModel(model);
      expect(content.ownerPhone, isEmpty);
      expect(content.isOwnerPhoneRevealed, isTrue);
      expect(PropertyDetailsModel.fromJson(model.toJson()), model);
    },
  );

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
