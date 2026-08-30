part of '../../imports.dart';

enum TenantVisitStatus { accepted, pending, rejected }

enum TenantVisitFilter { all, accepted, pending, rejected }

extension TenantVisitStatusX on TenantVisitStatus {
  bool get isAccepted => this == TenantVisitStatus.accepted;
  bool get isPending => this == TenantVisitStatus.pending;
  bool get isRejected => this == TenantVisitStatus.rejected;

  static TenantVisitStatus fromApiValue(String? value) {
    final String normalized = value?.trim().toLowerCase() ?? '';
    switch (normalized) {
      case 'accepted':
      case 'approved':
      case 'confirmed':
      case 'مقبول':
      case 'مؤكد':
        return TenantVisitStatus.accepted;
      case 'pending':
      case 'waiting':
      case 'awaiting_owner':
      case 'بانتظار الرد':
      case 'بانتظار رد المالك':
        return TenantVisitStatus.pending;
      case 'rejected':
      case 'declined':
      case 'مرفوض':
      default:
        return TenantVisitStatus.rejected;
    }
  }

  String get label {
    if (isAccepted) {
      return LocaleKeys.tenantVisitStatusAccepted;
    }
    if (isPending) {
      return LocaleKeys.tenantVisitStatusPending;
    }
    return LocaleKeys.tenantVisitStatusRejected;
  }
}

extension TenantVisitFilterX on TenantVisitFilter {
  bool get isAll => this == TenantVisitFilter.all;
  bool get isAccepted => this == TenantVisitFilter.accepted;
  bool get isPending => this == TenantVisitFilter.pending;
  bool get isRejected => this == TenantVisitFilter.rejected;

  String? get apiValue {
    if (isAll) return null;
    return name;
  }

  String get label {
    if (isAll) {
      return LocaleKeys.tenantVisitsFilterAll;
    }
    if (isAccepted) {
      return LocaleKeys.tenantVisitsFilterAccepted;
    }
    if (isPending) {
      return LocaleKeys.tenantVisitsFilterPending;
    }
    return LocaleKeys.tenantVisitsFilterRejected;
  }

  bool accepts(TenantVisitStatus status) {
    return isAll ||
        (isAccepted && status.isAccepted) ||
        (isPending && status.isPending) ||
        (isRejected && status.isRejected);
  }

  bool isSame(TenantVisitFilter other) {
    return (isAll && other.isAll) ||
        (isAccepted && other.isAccepted) ||
        (isPending && other.isPending) ||
        (isRejected && other.isRejected);
  }
}
