/// isNull extension to show if this [object] is null or not
extension NullChecker on Object?{

  /// isNull function to show if this [object] is null or not
  bool get isNull{
    return this == null;
  }

  /// isNull function to show if this [object] is not null or not
  bool get isNotNull{
    return this != null;
  }
}