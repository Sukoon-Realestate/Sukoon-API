import 'package:melos_core/config/language/locale_keys.g.dart';

enum OwnerVisitRequestStatus {
  newRequest,
  pending,
  accepted,
  rejected,
  canceled,
  completed,
}

extension OwnerVisitRequestStatusExtension on OwnerVisitRequestStatus {
  bool get isNewRequest => this == OwnerVisitRequestStatus.newRequest;
  bool get isPending => this == OwnerVisitRequestStatus.pending;
  bool get isAccepted => this == OwnerVisitRequestStatus.accepted;
  bool get isRejected => this == OwnerVisitRequestStatus.rejected;
  bool get isCanceled => this == OwnerVisitRequestStatus.canceled;
  bool get isCompleted => this == OwnerVisitRequestStatus.completed;
  bool get canDecide => isNewRequest || isPending;

  static OwnerVisitRequestStatus fromName(String? value) {
    switch (value) {
      case 'new':
      case 'new_request':
      case 'requested':
        return OwnerVisitRequestStatus.newRequest;
      case 'accepted':
      case 'confirmed':
        return OwnerVisitRequestStatus.accepted;
      case 'rejected':
        return OwnerVisitRequestStatus.rejected;
      case 'canceled':
      case 'cancelled':
        return OwnerVisitRequestStatus.canceled;
      case 'completed':
        return OwnerVisitRequestStatus.completed;
      case 'pending':
      default:
        return OwnerVisitRequestStatus.pending;
    }
  }

  String get label {
    if (isNewRequest) {
      return LocaleKeys.ownerVisitStatusNew;
    }
    if (isPending) {
      return LocaleKeys.ownerVisitStatusPending;
    }
    if (isAccepted) {
      return LocaleKeys.ownerVisitStatusAccepted;
    }
    if (isRejected) {
      return LocaleKeys.ownerVisitStatusRejected;
    }
    if (isCanceled) {
      return LocaleKeys.cancelled;
    }
    return LocaleKeys.ownerVisitStatusCompleted;
  }
}

enum OwnerVisitRequestFilter { all, newRequests, accepted, rejected, completed }

extension OwnerVisitRequestFilterExtension on OwnerVisitRequestFilter {
  bool get isAll => this == OwnerVisitRequestFilter.all;
  bool get isNewRequests => this == OwnerVisitRequestFilter.newRequests;
  bool get isAccepted => this == OwnerVisitRequestFilter.accepted;
  bool get isRejected => this == OwnerVisitRequestFilter.rejected;
  bool get isCompleted => this == OwnerVisitRequestFilter.completed;

  String get label {
    if (isAll) {
      return LocaleKeys.ownerVisitsFilterAll;
    }
    if (isNewRequests) {
      return LocaleKeys.ownerVisitsFilterNew;
    }
    if (isAccepted) {
      return LocaleKeys.ownerVisitsFilterAccepted;
    }
    if (isRejected) {
      return LocaleKeys.ownerVisitsFilterRejected;
    }
    return LocaleKeys.ownerVisitsFilterCompleted;
  }

  bool accepts(OwnerVisitRequestStatus status) {
    if (isAll) {
      return true;
    }
    if (isNewRequests) {
      return status.isNewRequest || status.isPending;
    }
    if (isAccepted) {
      return status.isAccepted;
    }
    if (isRejected) {
      return status.isRejected;
    }
    return status.isCompleted;
  }

  bool isSame(OwnerVisitRequestFilter other) => this == other;
}

enum OwnerRequestResolution { accepted, rejected }

extension OwnerRequestResolutionExtension on OwnerRequestResolution {
  bool get isAccepted => this == OwnerRequestResolution.accepted;
  bool get isRejected => this == OwnerRequestResolution.rejected;
}

enum OwnerAvailabilitySlotState { unspecified, available, booked }

extension OwnerAvailabilitySlotStateExtension on OwnerAvailabilitySlotState {
  bool get isUnspecified => this == OwnerAvailabilitySlotState.unspecified;
  bool get isAvailable => this == OwnerAvailabilitySlotState.available;
  bool get isBooked => this == OwnerAvailabilitySlotState.booked;

  String get label {
    if (isAvailable) {
      return LocaleKeys.ownerAvailabilityAvailable;
    }
    if (isBooked) {
      return LocaleKeys.ownerAvailabilityBooked;
    }
    return LocaleKeys.ownerAvailabilityUnspecified;
  }
}
