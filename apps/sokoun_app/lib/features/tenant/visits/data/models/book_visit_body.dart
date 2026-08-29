part of '../../imports.dart';

class BookVisitBody extends Equatable {
  const BookVisitBody({
    required this.visitDate,
    required this.visitTime,
    required this.note,
  });

  const BookVisitBody.initial() : visitDate = '', visitTime = '', note = '';

  factory BookVisitBody.fromTime({
    required String visitDate,
    required int hour,
    required int minute,
    required String note,
  }) {
    return BookVisitBody(
      visitDate: visitDate,
      visitTime: formatApiTime(hour: hour, minute: minute),
      note: note,
    );
  }

  final String visitDate;
  final String visitTime;
  final String note;

  static String formatDisplayTime({required int hour, required int minute}) {
    final int displayHour = hour % 12 == 0 ? 12 : hour % 12;
    final String displayMinute = minute.toString().padLeft(2, '0');
    final String period = hour < 12 ? 'AM' : 'PM';
    return '$displayHour:$displayMinute $period';
  }

  static String formatApiTime({required int hour, required int minute}) {
    final String apiHour = hour.toString().padLeft(2, '0');
    final String apiMinute = minute.toString().padLeft(2, '0');
    return '$apiHour:$apiMinute';
  }

  Map<String, dynamic> toJson() => {
    'visit_date': visitDate,
    'visit_time': visitTime,
    'note': note,
  };

  BookVisitBody copyWith({String? visitDate, String? visitTime, String? note}) {
    return BookVisitBody(
      visitDate: visitDate ?? this.visitDate,
      visitTime: visitTime ?? this.visitTime,
      note: note ?? this.note,
    );
  }

  @override
  List<Object?> get props => [visitDate, visitTime, note];
}
