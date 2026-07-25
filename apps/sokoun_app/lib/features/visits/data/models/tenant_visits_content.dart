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

  static List<VisitDayContent> get days => [
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDayFriday,
      day: '14',
      month: LocaleKeys.tenantVisitMonthJune,
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDaySaturday,
      day: '15',
      month: LocaleKeys.tenantVisitMonthJune,
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDaySunday,
      day: '16',
      month: LocaleKeys.tenantVisitMonthJune,
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDayMonday,
      day: '17',
      month: LocaleKeys.tenantVisitMonthJune,
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDayTuesday,
      day: '18',
      month: LocaleKeys.tenantVisitMonthJune,
    ),
  ];

  static List<VisitTimeSlotContent> get timeSlots => [
    VisitTimeSlotContent(label: LocaleKeys.tenantVisitTimeTenAm),
    VisitTimeSlotContent(label: LocaleKeys.tenantVisitTimeElevenAm),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeNoon,
      isAvailable: false,
    ),
    VisitTimeSlotContent(label: LocaleKeys.tenantVisitTimeTwoPm),
    VisitTimeSlotContent(label: LocaleKeys.tenantVisitTimeThreePm),
    VisitTimeSlotContent(label: LocaleKeys.tenantVisitTimeFivePm),
  ];
}
