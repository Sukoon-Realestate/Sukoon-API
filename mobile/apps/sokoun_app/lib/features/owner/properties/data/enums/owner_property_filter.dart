import 'owner_property_status.dart';

enum OwnerPropertyFilter { underReview, accepted, rejected }

extension OwnerPropertyFilterX on OwnerPropertyFilter {
  String get apiValue => switch (this) {
    OwnerPropertyFilter.underReview => 'under_review',
    OwnerPropertyFilter.accepted => 'accepted',
    OwnerPropertyFilter.rejected => 'rejected',
  };

  bool accepts(OwnerPropertyStatus status) => switch (this) {
    OwnerPropertyFilter.underReview => status.isPending,
    OwnerPropertyFilter.accepted => status.isAccepted || status.isVerified,
    OwnerPropertyFilter.rejected => status.isRejected,
  };
}
