part of '../../imports.dart';

abstract final class TenantVisitsContent {
  static List<TenantVisitContent> get visits => [
    TenantVisitContent(
      id: 'accepted-nasr-city',
      propertyTitle: LocaleKeys.tenantVisitPropertyNasrCity,
      ownerName: LocaleKeys.tenantVisitOwnerAhmed,
      dateLabel: LocaleKeys.tenantVisitDateToday,
      status: TenantVisitStatus.accepted,
      detailDate: LocaleKeys.tenantVisitDetailDate,
      time: LocaleKeys.tenantVisitTimeTwoPm,
      ownerPhone: LocaleKeys.tenantVisitDetailPhone,
    ),
    TenantVisitContent(
      id: 'pending-fifth-settlement',
      propertyTitle: LocaleKeys.tenantVisitPropertyFifthSettlement,
      ownerName: LocaleKeys.tenantVisitOwnerMona,
      dateLabel: LocaleKeys.tenantVisitDateTomorrow,
      status: TenantVisitStatus.pending,
      detailDate: LocaleKeys.tenantVisitDateTomorrow,
      time: LocaleKeys.tenantVisitTimeNoon,
      ownerPhone: '',
    ),
    TenantVisitContent(
      id: 'rejected-mohandessin',
      propertyTitle: LocaleKeys.tenantVisitPropertyMohandessin,
      ownerName: LocaleKeys.tenantVisitOwnerKhaled,
      dateLabel: LocaleKeys.tenantVisitDateThursday,
      status: TenantVisitStatus.rejected,
      detailDate: LocaleKeys.tenantVisitDateThursday,
      time: LocaleKeys.tenantVisitTimeFivePm,
      ownerPhone: '',
    ),
  ];
}
