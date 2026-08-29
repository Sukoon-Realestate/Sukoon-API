import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

void main() {
  group('mobile API handoff models', () {
    test('parses available places and accepts an empty places list', () {
      final AvailablePlacesModel places = AvailablePlacesModel.fromJson({
        'places': [
          {'country': 'Egypt', 'city': 'Cairo', 'district': 'Maadi'},
        ],
      });

      expect(places.places, hasLength(1));
      expect(places.places.single.searchQuery, 'Maadi، Cairo، Egypt');
      expect(AvailablePlacesModel.fromJson({'places': []}).places, isEmpty);
    });

    test('parses the new property details state and amenities contract', () {
      final PropertyDetailsModel property = PropertyDetailsModel.fromJson({
        'id': 'property-uuid',
        'title': 'Furnished apartment',
        'is_furnished': true,
        'amenities': ['wifi', 'garage', 'security'],
        'is_fav': true,
        'is_saved': false,
        'rating': 4.7,
        'has_elevator': true,
      });

      expect(property.amenities, ['wifi', 'garage', 'security']);
      expect(property.isFav, isTrue);
      expect(property.isSaved, isFalse);
      expect(property.rating, 4.7);
      expect(property.toJson(), isNot(contains('has_elevator')));
      expect(const PropertyDetailsModel.initial().rating, 0);
    });

    test('parses schedule display and machine values separately', () {
      final VisitScheduleContent schedule = VisitScheduleContent.fromJson({
        'days': [
          {'day': 'tuesday', 'date': '15/9', 'visit_date': '2026-09-15'},
        ],
        'times': [
          {'time': '10:00 AM', 'visit_time': '10:00:00', 'is_available': true},
          {'time': '11:00 AM', 'visit_time': '11:00:00', 'is_available': false},
        ],
      });

      expect(schedule.days.single.day, '15');
      expect(schedule.days.single.month, '9');
      expect(schedule.days.single.visitDate, '2026-09-15');
      expect(schedule.times.first.label, '10:00 AM');
      expect(schedule.times.first.visitTime, '10:00:00');
      expect(schedule.times.last.isAvailable, isFalse);
      expect(const VisitScheduleContent.initial().days, isEmpty);
      expect(const VisitScheduleContent.initial().times, isEmpty);
    });

    test('books with machine values and identifies slot conflicts', () {
      const BookVisitBody body = BookVisitBody(
        visitDate: '2026-09-15',
        visitTime: '10:00:00',
        note: 'Optional tenant note',
      );

      expect(body.toJson(), {
        'visit_date': '2026-09-15',
        'visit_time': '10:00:00',
        'note': 'Optional tenant note',
      });
      expect(
        BookVisitCubit.isUnavailableSlotError(
          'The selected visit slot is already booked.',
        ),
        isTrue,
      );
      expect(
        BookVisitCubit.isUnavailableSlotError(
          'The selected visit slot is not available.',
        ),
        isTrue,
      );
    });
  });
}
