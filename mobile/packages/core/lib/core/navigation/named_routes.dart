enum NamedRoutes {
  splash('/'),
  oldPhoneOtpScreen('/oldPhoneOtpScreen'),
  newPhoneOtpScreen('/newPhoneOtpScreen'),
  changePhone('/ChangePhoneSheetBody'),
  editParentProfile('/editParentProfile');

  final String routeName;
  const NamedRoutes(this.routeName);
}
