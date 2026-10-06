abstract interface class SessionAuthService {
  Future<Uri?> getBaseUri();

  Future<String?> getAccessToken();

  Future<bool> refreshSession();
}
