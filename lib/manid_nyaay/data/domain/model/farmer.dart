class Farmer {
  final String id;
  final String name;
  final String phone;
  final String village;
  final String taluka;
  final String district;
  final int totalSupplies;
  final String lastSupply;

  const Farmer({
    required this.id,
    required this.name,
    required this.phone,
    required this.village,
    required this.taluka,
    required this.district,
    required this.totalSupplies,
    required this.lastSupply,
  });

  // Adding copyWith to replicate Kotlin's data class .copy() functionality
  Farmer copyWith({
    String? id,
    String? name,
    String? phone,
    String? village,
    String? taluka,
    String? district,
    int? totalSupplies,
    String? lastSupply,
  }) {
    return Farmer(
      id: id ?? this.id,
      name: name ?? this.name,
      phone: phone ?? this.phone,
      village: village ?? this.village,
      taluka: taluka ?? this.taluka,
      district: district ?? this.district,
      totalSupplies: totalSupplies ?? this.totalSupplies,
      lastSupply: lastSupply ?? this.lastSupply,
    );
  }
}