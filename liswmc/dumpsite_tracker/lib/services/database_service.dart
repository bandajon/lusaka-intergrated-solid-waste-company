import 'package:postgres/postgres.dart';
import 'dart:async';
import '../models/vehicle.dart';
import '../models/company.dart';
import '../models/visit_record.dart';
import '../models/neighborhood.dart';

class DatabaseService {
  PostgreSQLConnection? _connection;
  final String _connectionString = 'postgresql://agripredict:Wee8fdm0k2!!@agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com:5432/users';
  
  Future<void> initialize() async {
    try {
      // Parse connection string
      Uri uri = Uri.parse(_connectionString.replaceFirst('postgresql://', 'http://'));
      
      _connection = PostgreSQLConnection(
        uri.host,
        uri.port,
        uri.path.replaceFirst('/', ''),
        username: uri.userInfo.split(':')[0],
        password: uri.userInfo.split(':')[1],
        useSSL: true,
      );
      
      await _connection?.open();
      print('Database connection established');
      
      // Initialize tables if they don't exist
      await _ensureTablesExist();
    } catch (e) {
      print('Error connecting to database: $e');
      throw Exception('Failed to connect to database: $e');
    }
  }
  
  Future<void> _ensureTablesExist() async {
    await _connection?.execute('''
      CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL CHECK (type IN ('Franchise', 'Community', 'LISWMC', 'Private')),
        contact_person VARCHAR(255),
        contact_number VARCHAR(20),
        email VARCHAR(255),
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'Active'
      )
    ''');
    
    await _connection?.execute('''
      CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        license_plate VARCHAR(20) NOT NULL UNIQUE,
        company_id INTEGER REFERENCES companies(id),
        vehicle_type VARCHAR(100),
        vehicle_image_url TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_temporary BOOLEAN DEFAULT FALSE,
        temp_expiry_date TIMESTAMP,
        last_visit_date TIMESTAMP
      )
    ''');
    
    await _connection?.execute('''
      CREATE TABLE IF NOT EXISTS neighborhoods (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        zone VARCHAR(100),
        city VARCHAR(100) DEFAULT 'Lusaka'
      )
    ''');
    
    await _connection?.execute('''
      CREATE TABLE IF NOT EXISTS visit_records (
        id SERIAL PRIMARY KEY,
        vehicle_id INTEGER REFERENCES vehicles(id),
        entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_time TIMESTAMP,
        neighborhood_id INTEGER REFERENCES neighborhoods(id),
        waste_type VARCHAR(100),
        notes TEXT,
        created_by VARCHAR(255),
        image_url TEXT,
        offline_created BOOLEAN DEFAULT FALSE,
        sync_status VARCHAR(50) DEFAULT 'Synced'
      )
    ''');
  }
  
  Future<List<Vehicle>> searchVehicleByLicensePlate(String plate) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'SELECT v.*, c.name as company_name, c.type as company_type FROM vehicles v '
      'LEFT JOIN companies c ON v.company_id = c.id '
      'WHERE v.license_plate ILIKE @plate',
      substitutionValues: {'plate': '%$plate%'}
    );
    
    return results?.map((row) => Vehicle.fromMap({
      'id': row[0],
      'license_plate': row[1],
      'company_id': row[2],
      'vehicle_type': row[3],
      'vehicle_image_url': row[4],
      'registration_date': row[5],
      'is_temporary': row[6],
      'temp_expiry_date': row[7],
      'last_visit_date': row[8],
      'company_name': row[9],
      'company_type': row[10],
    })).toList() ?? [];
  }
  
  Future<Company?> getCompanyDetails(int companyId) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'SELECT * FROM companies WHERE id = @id',
      substitutionValues: {'id': companyId}
    );
    
    if (results == null || results.isEmpty) return null;
    
    final row = results.first;
    return Company.fromMap({
      'id': row[0],
      'name': row[1],
      'type': row[2],
      'contact_person': row[3],
      'contact_number': row[4],
      'email': row[5],
      'registration_date': row[6],
      'status': row[7],
    });
  }
  
  Future<int> registerNewCompany(Company company) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'INSERT INTO companies (name, type, contact_person, contact_number, email, status) '
      'VALUES (@name, @type, @contactPerson, @contactNumber, @email, @status) '
      'RETURNING id',
      substitutionValues: {
        'name': company.name,
        'type': company.type,
        'contactPerson': company.contactPerson,
        'contactNumber': company.contactNumber,
        'email': company.email,
        'status': company.status,
      }
    );
    
    return results?.first[0] as int? ?? -1;
  }
  
  Future<int> registerNewVehicle(Vehicle vehicle) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'INSERT INTO vehicles (license_plate, company_id, vehicle_type, vehicle_image_url, is_temporary, temp_expiry_date) '
      'VALUES (@plate, @companyId, @type, @imageUrl, @isTemp, @expiry) '
      'RETURNING id',
      substitutionValues: {
        'plate': vehicle.licensePlate,
        'companyId': vehicle.companyId,
        'type': vehicle.vehicleType,
        'imageUrl': vehicle.vehicleImageUrl,
        'isTemp': vehicle.isTemporary,
        'expiry': vehicle.tempExpiryDate,
      }
    );
    
    return results?.first[0] as int? ?? -1;
  }
  
  Future<int> saveVisitRecord(VisitRecord record) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'INSERT INTO visit_records (vehicle_id, entry_time, neighborhood_id, waste_type, notes, created_by, image_url, offline_created, sync_status) '
      'VALUES (@vehicleId, @entryTime, @neighborhoodId, @wasteType, @notes, @createdBy, @imageUrl, @offlineCreated, @syncStatus) '
      'RETURNING id',
      substitutionValues: {
        'vehicleId': record.vehicleId,
        'entryTime': record.entryTime,
        'neighborhoodId': record.neighborhoodId,
        'wasteType': record.wasteType,
        'notes': record.notes,
        'createdBy': record.createdBy,
        'imageUrl': record.imageUrl,
        'offlineCreated': record.offlineCreated,
        'syncStatus': record.syncStatus,
      }
    );
    
    if (results != null && results.isNotEmpty) {
      final id = results.first[0] as int;
      
      // Update the vehicle's last visit date
      await _connection?.execute(
        'UPDATE vehicles SET last_visit_date = @date WHERE id = @id',
        substitutionValues: {
          'date': record.entryTime,
          'id': record.vehicleId,
        }
      );
      
      return id;
    }
    
    return -1;
  }
  
  Future<bool> updateVisitRecordExitTime(int recordId, DateTime exitTime) async {
    if (_connection == null) await initialize();
    
    final result = await _connection?.execute(
      'UPDATE visit_records SET exit_time = @exitTime WHERE id = @id',
      substitutionValues: {
        'exitTime': exitTime,
        'id': recordId,
      }
    );
    
    return (result ?? 0) > 0;
  }
  
  Future<List<Neighborhood>> searchNeighborhoods(String query) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'SELECT * FROM neighborhoods WHERE name ILIKE @query ORDER BY name',
      substitutionValues: {'query': '%$query%'}
    );
    
    return results?.map((row) => Neighborhood.fromMap({
      'id': row[0],
      'name': row[1],
      'zone': row[2],
      'city': row[3],
    })).toList() ?? [];
  }
  
  Future<List<VisitRecord>> getRecentVisits({int limit = 50, int offset = 0}) async {
    if (_connection == null) await initialize();
    
    final results = await _connection?.query(
      'SELECT vr.*, v.license_plate, c.name as company_name, n.name as neighborhood_name '
      'FROM visit_records vr '
      'JOIN vehicles v ON vr.vehicle_id = v.id '
      'LEFT JOIN companies c ON v.company_id = c.id '
      'LEFT JOIN neighborhoods n ON vr.neighborhood_id = n.id '
      'ORDER BY vr.entry_time DESC '
      'LIMIT @limit OFFSET @offset',
      substitutionValues: {
        'limit': limit,
        'offset': offset,
      }
    );
    
    return results?.map((row) => VisitRecord.fromMap({
      'id': row[0],
      'vehicle_id': row[1],
      'entry_time': row[2],
      'exit_time': row[3],
      'neighborhood_id': row[4],
      'waste_type': row[5],
      'notes': row[6],
      'created_by': row[7],
      'image_url': row[8],
      'offline_created': row[9],
      'sync_status': row[10],
      'license_plate': row[11],
      'company_name': row[12],
      'neighborhood_name': row[13],
    })).toList() ?? [];
  }
  
  Future<void> close() async {
    await _connection?.close();
  }
}