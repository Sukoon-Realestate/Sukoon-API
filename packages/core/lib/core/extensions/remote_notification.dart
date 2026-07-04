import 'package:firebase_messaging/firebase_messaging.dart';

extension Exetract on RemoteMessage{
  int get getCurrentStageAsInt => data['stage'];
}