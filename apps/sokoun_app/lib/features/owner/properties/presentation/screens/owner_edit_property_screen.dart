part of '../../imports.dart';

class OwnerEditPropertyScreen extends StatelessWidget {
  const OwnerEditPropertyScreen({super.key, required this.property});

  final PropertyDetailsModel property;

  @override
  Widget build(BuildContext context) {
    return OwnerPropertyFlowScreen(property: property);
  }
}
