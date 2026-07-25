class FavoritePropertyContent {
  const FavoritePropertyContent({
    required this.id,
    required this.title,
    required this.price,
    required this.rating,
    required this.area,
  });

  factory FavoritePropertyContent.initial() => const FavoritePropertyContent(
    id: 0,
    title: '',
    price: '',
    rating: '',
    area: '',
  );

  factory FavoritePropertyContent.fromJson(Map<String, dynamic> json) {
    return FavoritePropertyContent(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      price: json['price'] ?? '',
      rating: json['rating'] ?? '',
      area: json['area'] ?? '',
    );
  }

  final int id;
  final String title;
  final String price;
  final String rating;
  final String area;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'price': price,
      'rating': rating,
      'area': area,
    };
  }

  FavoritePropertyContent copyWith({
    int? id,
    String? title,
    String? price,
    String? rating,
    String? area,
  }) {
    return FavoritePropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
      price: price ?? this.price,
      rating: rating ?? this.rating,
      area: area ?? this.area,
    );
  }
}

abstract final class FavoritesContent {
  static const List<FavoritePropertyContent> initialItems = [
    FavoritePropertyContent(
      id: 1,
      title: 'شقة مفروشة — مدينة نصر',
      price: '6,500',
      rating: '4.8',
      area: '90م²',
    ),
    FavoritePropertyContent(
      id: 2,
      title: 'ستوديو عصري — التجمع',
      price: '4,200',
      rating: '4.6',
      area: '55م²',
    ),
    FavoritePropertyContent(
      id: 3,
      title: 'شقة 3 غرف — المهندسين',
      price: '8,800',
      rating: '4.9',
      area: '120م²',
    ),
  ];
}
