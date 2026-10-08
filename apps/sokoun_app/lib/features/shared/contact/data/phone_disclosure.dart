/// Visit acceptance is a legacy fallback when a visit payload omits permission.
/// Conversations and public property reads require an explicit server grant.
abstract final class PhoneDisclosure {
  static String revealedPhone({
    required String phoneNumber,
    bool? isPhoneRevealed,
    bool hasAcceptedVisit = false,
  }) {
    if (!(isPhoneRevealed ?? hasAcceptedVisit)) return '';
    final String phone = phoneNumber.trim();
    // A masked value must never become a displayed or callable contact number.
    if (!RegExp(r'^\+?[0-9\s().-]+$').hasMatch(phone) ||
        !RegExp(r'[0-9]').hasMatch(phone)) {
      return '';
    }
    return phone;
  }
}
