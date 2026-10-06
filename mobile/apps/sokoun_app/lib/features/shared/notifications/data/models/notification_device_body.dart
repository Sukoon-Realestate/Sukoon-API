class NotificationDeviceBody {
  const NotificationDeviceBody({
    required this.token,
    required this.deviceType,
    this.deviceName,
  });

  final String token;
  final String deviceType;
  final String? deviceName;

  Map<String, dynamic> toJson() => {
    'token': token,
    'device_type': deviceType,
    if (deviceName?.trim().isNotEmpty == true) 'device_name': deviceName,
  };
}
