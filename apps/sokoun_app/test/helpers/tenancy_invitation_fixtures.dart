import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';

Map<String, dynamic> invitationJson({
  String owner = 'fixture-account',
  String tenant = 'tenant-a',
  RentalSelection? selection,
}) => {
  'id': 'invitation-a',
  'property_id': 'property-a',
  'property_title': 'شقة المعادي',
  'owner_id': owner,
  'owner_name': 'المالك',
  'tenant_id': tenant,
  'tenant_name': 'المستأجر',
  if (selection != null) ...{
    'offer_id': selection.offerId,
    'offer_snapshot': selection.toJson(),
  },
  'status': 'pending',
  'revision': 1,
  'created_at': '2026-10-08T09:00:00Z',
  'expires_at': '2099-10-15T09:00:00Z',
  'eligible_for_lease': false,
  'actions': {'can_respond': tenant == 'fixture-account'},
};
