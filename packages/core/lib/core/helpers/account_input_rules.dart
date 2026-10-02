/// Syntax checks shared by account forms and their request data.
/// Server-side validation remains responsible for uniqueness and verification.
class AccountInputRules {
  static const int nameMaxLength = 50;
  static const int emailMaxLength = 254;
  static const int passwordMinLength = 8;
  static const int otpLength = 6;

  static final RegExp _name = RegExp(
    r"^\p{L}[\p{L}\p{M}]*(?: +\p{L}[\p{L}\p{M}]*|['’\-]\p{L}[\p{L}\p{M}]*)*$",
    unicode: true,
  );
  static final RegExp _emailLocalPart = RegExp(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+)*$",
  );
  static final RegExp _domainLabel = RegExp(
    r'^[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?$',
  );

  static bool isValidName(String value) {
    final String name = value.trim();
    return name.runes.length <= nameMaxLength && _name.hasMatch(name);
  }

  static bool isValidEmail(String value) {
    final String email = value.trim();
    if (email.length > emailMaxLength) return false;
    final List<String> parts = email.split('@');
    if (parts.length != 2 || parts.first.length > 64) return false;
    if (!_emailLocalPart.hasMatch(parts.first)) return false;

    final List<String> labels = parts.last.split('.');
    return labels.length >= 2 &&
        labels.every(
          (label) => label.length <= 63 && _domainLabel.hasMatch(label),
        ) &&
        RegExp(r'^[a-zA-Z]{2,}$').hasMatch(labels.last);
  }

  /// Local Egyptian mobile format; country-code forms need a server contract.
  static bool isValidEgyptianMobile(String value) =>
      RegExp(r'^01[0125][0-9]{8}$').hasMatch(value.trim());

  static bool isValidOtpCode(String value, {int length = otpLength}) =>
      length > 0 &&
      value.length == length &&
      RegExp(r'^[0-9]+$').hasMatch(value);

  /// Format only; identity/date/document authenticity is checked by the server.
  static bool isValidEgyptianNationalId(String value) =>
      RegExp(r'^[0-9]{14}$').hasMatch(value.trim());
}
