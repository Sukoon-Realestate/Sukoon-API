import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';

void main() {
  for (final field in ['message', 'msg']) {
    test('preserves the backend $field without changing its text or data', () {
      final response = BaseModel<String>.fromJson({
        'key': 'success',
        field: 'تم إنشاء الدعوة.',
        'data': 'invitation-a',
      }, jsonToModel: (data) => data as String);
      expect(response.key, 'success');
      expect(response.msg, 'تم إنشاء الدعوة.');
      expect(response.data, 'invitation-a');
    });
  }
  test('keeps message priority when both envelope fields are provided', () {
    final response = BaseModel<String>.fromJson({
      'message': 'Current wording',
      'msg': 'Legacy wording',
      'data': 'invitation-a',
    });
    expect(response.msg, 'Current wording');
  });
  test('does not invent text when both message fields are absent', () {
    expect(BaseModel<String>.fromJson({'data': 'invitation-a'}).msg, isEmpty);
  });
}
