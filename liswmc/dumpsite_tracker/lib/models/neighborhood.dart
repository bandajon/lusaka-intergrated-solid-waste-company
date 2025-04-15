class Neighborhood {
  final int? id;
  final String name;
  final String? zone;
  final String city;

  Neighborhood({
    this.id,
    required this.name,
    this.zone,
    this.city = 'Lusaka',
  });

  factory Neighborhood.fromMap(Map<String, dynamic> map) {
    return Neighborhood(
      id: map['id'],
      name: map['name'],
      zone: map['zone'],
      city: map['city'] ?? 'Lusaka',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'zone': zone,
      'city': city,
    };
  }

  @override
  String toString() {
    return 'Neighborhood(id: $id, name: $name, zone: $zone, city: $city)';
  }
}