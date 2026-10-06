/// Authentication and identity documents must never enter diagnostics payloads.
abstract final class NetworkLoggingPolicy {
  static bool isSensitive(String path) => path.split('/').contains('auth');

  static Map<String, dynamic> safeHeaders(Map<String, dynamic> headers) => {
    for (final entry in headers.entries)
      entry.key: switch (entry.key.toLowerCase()) {
        'authorization' || 'cookie' || 'set-cookie' => '[redacted]',
        _ => entry.value,
      },
  };
}
