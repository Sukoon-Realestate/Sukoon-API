import 'package:equatable/equatable.dart';

class WorkspaceCounts extends Equatable {
  const WorkspaceCounts({required this.favorites, required this.visits});
  const WorkspaceCounts.initial() : favorites = 0, visits = 0;

  factory WorkspaceCounts.fromJson(Map<String, dynamic> json) =>
      WorkspaceCounts(
        favorites: (json['favorites_count'] as num?)?.toInt() ?? 0,
        visits: (json['visit_requests_count'] as num?)?.toInt() ?? 0,
      );

  final int favorites;
  final int visits;

  Map<String, dynamic> toJson() => {
    'favorites_count': favorites,
    'visit_requests_count': visits,
  };

  WorkspaceCounts copyWith({int? favorites, int? visits}) => WorkspaceCounts(
    favorites: favorites ?? this.favorites,
    visits: visits ?? this.visits,
  );

  @override
  List<Object?> get props => [favorites, visits];
}
