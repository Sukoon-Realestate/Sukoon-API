/// Only the server's viewer-specific grant authorizes contact disclosure.
/// A visit's current status cannot establish a historical acceptance grant.
abstract final class PhoneDisclosure {
  static String revealedPhone({
    required String phoneNumber,
    bool? isPhoneRevealed,
  }) {
    if (isPhoneRevealed != true) return '';
    final String phone = phoneNumber.trim();
    // A masked value must never become a displayed or callable contact number.
    if (!RegExp(r'^\+?[0-9\s().-]+$').hasMatch(phone) ||
        !RegExp(r'[0-9]').hasMatch(phone)) {
      return '';
    }
    return phone;
  }
}
