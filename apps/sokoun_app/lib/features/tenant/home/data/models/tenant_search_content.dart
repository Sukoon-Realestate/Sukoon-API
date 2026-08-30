import 'package:equatable/equatable.dart';

class RecentSearchContent extends Equatable {
  const RecentSearchContent({required this.title});

  const RecentSearchContent.initial() : title = '';

  factory RecentSearchContent.fromJson(Map<String, dynamic> json) {
    return RecentSearchContent(title: json['title'] as String? ?? '');
  }

  final String title;

  Map<String, dynamic> toJson() => {'title': title};

  RecentSearchContent copyWith({String? title}) {
    return RecentSearchContent(title: title ?? this.title);
  }

  @override
  List<Object?> get props => [title];
}

class TenantSearchFormState {
  const TenantSearchFormState({
    required this.selectedCategory,
    required this.selectedArea,
  });

  const TenantSearchFormState.initial()
    : selectedCategory = '',
      selectedArea = null;

  final String selectedCategory;
  final String? selectedArea;

  TenantSearchFormState copyWith({
    String? selectedCategory,
    String? selectedArea,
    bool clearSelectedArea = false,
  }) {
    return TenantSearchFormState(
      selectedCategory: selectedCategory ?? this.selectedCategory,
      selectedArea: clearSelectedArea
          ? null
          : selectedArea ?? this.selectedArea,
    );
  }
}
