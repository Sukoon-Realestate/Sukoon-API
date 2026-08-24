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
      visitDate: '2026-06-14',
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDaySaturday,
      day: '15',
      month: LocaleKeys.tenantVisitMonthJune,
      visitDate: '2026-06-15',
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDaySunday,
      day: '16',
      month: LocaleKeys.tenantVisitMonthJune,
      visitDate: '2026-06-16',
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDayMonday,
      day: '17',
      month: LocaleKeys.tenantVisitMonthJune,
      visitDate: '2026-06-17',
    ),
    VisitDayContent(
      weekday: LocaleKeys.tenantVisitDayTuesday,
      day: '18',
      month: LocaleKeys.tenantVisitMonthJune,
      visitDate: '2026-06-18',
    ),
  ];

  static List<VisitTimeSlotContent> get timeSlots => [
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeTenAm,
      visitTime: '10:00:00',
    ),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeElevenAm,
      visitTime: '11:00:00',
    ),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeNoon,
      visitTime: '12:00:00',
      isAvailable: false,
    ),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeTwoPm,
      visitTime: '14:00:00',
    ),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeThreePm,
      visitTime: '15:00:00',
    ),
    VisitTimeSlotContent(
      label: LocaleKeys.tenantVisitTimeFivePm,
      visitTime: '17:00:00',
    ),
  ];
}
