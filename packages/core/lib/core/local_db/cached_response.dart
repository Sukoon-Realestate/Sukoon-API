import 'package:objectbox/objectbox.dart';

@Entity()
class CachedResponse {
  @Id()
  int id = 0;

  @Unique()
  late String key;

  late String jsonValue;

  CachedResponse({required this.key, required this.jsonValue});

  CachedResponse.empty();
}
