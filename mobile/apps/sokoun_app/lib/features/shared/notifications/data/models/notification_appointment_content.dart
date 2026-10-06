import 'package:equatable/equatable.dart';

class NotificationAppointmentContent extends Equatable {
  const NotificationAppointmentContent({
    required this.title,
    required this.dateTimeLabel,
    required this.locationLabel,
  });

  const NotificationAppointmentContent.initial()
    : title = '',
      dateTimeLabel = '',
      locationLabel = '';

  factory NotificationAppointmentContent.fromJson(Map<String, dynamic> json) {
    return NotificationAppointmentContent(
      title: json['title']?.toString() ?? '',
      dateTimeLabel: json['datetime_label']?.toString() ?? '',
      locationLabel: json['location_label']?.toString() ?? '',
    );
  }

  final String title;
  final String dateTimeLabel;
  final String locationLabel;

  bool get isEmpty =>
      title.trim().isEmpty &&
      dateTimeLabel.trim().isEmpty &&
      locationLabel.trim().isEmpty;

  Map<String, dynamic> toJson() => {
    'title': title,
    'datetime_label': dateTimeLabel,
    'location_label': locationLabel,
  };

  NotificationAppointmentContent copyWith({
    String? title,
    String? dateTimeLabel,
    String? locationLabel,
  }) {
    return NotificationAppointmentContent(
      title: title ?? this.title,
      dateTimeLabel: dateTimeLabel ?? this.dateTimeLabel,
      locationLabel: locationLabel ?? this.locationLabel,
    );
  }

  @override
  List<Object?> get props => [title, dateTimeLabel, locationLabel];
}
