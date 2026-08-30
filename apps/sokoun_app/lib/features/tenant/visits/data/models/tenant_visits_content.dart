part of '../../imports.dart';

abstract final class TenantVisitsContent {
  static List<TenantVisitContent> get visits => [
    TenantVisitContent(
      id: 'accepted-nasr-city',
      propertyTitle: LocaleKeys.tenantVisitPropertyNasrCity,
      day: LocaleKeys.tenantVisitDetailDate,
      time: LocaleKeys.tenantVisitTimeTwoPm,
      status: TenantVisitStatus.accepted,
      statusText: LocaleKeys.tenantVisitStatusAccepted,
      ownerName: LocaleKeys.tenantVisitOwnerAhmed,
      ownerPhone: LocaleKeys.tenantVisitDetailPhone,
    ),
    TenantVisitContent(
      id: 'pending-fifth-settlement',
      propertyTitle: LocaleKeys.tenantVisitPropertyFifthSettlement,
      day: LocaleKeys.tenantVisitDateTomorrow,
      time: LocaleKeys.tenantVisitTimeNoon,
      status: TenantVisitStatus.pending,
      statusText: LocaleKeys.tenantVisitStatusPending,
      ownerName: LocaleKeys.tenantVisitOwnerMona,
    ),
    TenantVisitContent(
      id: 'rejected-mohandessin',
      propertyTitle: LocaleKeys.tenantVisitPropertyMohandessin,
      day: LocaleKeys.tenantVisitDateThursday,
      time: LocaleKeys.tenantVisitTimeFivePm,
      status: TenantVisitStatus.rejected,
      statusText: LocaleKeys.tenantVisitStatusRejected,
      ownerName: LocaleKeys.tenantVisitOwnerKhaled,
    ),
  ];
}
