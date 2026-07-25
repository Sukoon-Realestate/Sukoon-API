import 'package:flutter/material.dart';
import 'package:sokoun_app/features/properties/imports.dart';

/// Compatibility entry point for the original owner-listings route.
///
/// The complete O-PROPS flow now lives in the dedicated properties feature.
class OwnerListingsScreen extends StatelessWidget {
  const OwnerListingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const OwnerPropertiesScreen();
  }
}
