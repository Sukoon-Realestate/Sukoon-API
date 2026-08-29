part of '../../imports.dart';

class BookVisitBody extends Equatable {
  const BookVisitBody({
    required this.visitDate,
    required this.visitTime,
    required this.note,
  });

  const BookVisitBody.initial() : visitDate = '', visitTime = '', note = '';

  final String visitDate;
  final String visitTime;
  final String note;

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
