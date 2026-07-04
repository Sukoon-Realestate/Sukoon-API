part of 'notification_service.dart';

class NotificationRoutes {

  static void navigateByType(Map<String, dynamic> data) {
    final String type = data['type'];
    log('the type is ${data['type']}');
    final NotificationType notificationType = type.getType;
    log('the type is $notificationType');
    notificationType.navigation.navigate(data: data);
  }
}

extension GetNotificationTypeById on String {
  NotificationType get getType {
    return NotificationType.values.firstWhere((element) => element.id == this);
  }
}

abstract interface class NotificationNavigation {
  void navigate({required Map<String, dynamic> data});
}

class NoNavigation implements NotificationNavigation{
  const NoNavigation();
  @override
  void navigate({required Map<String, dynamic> data}){}
}