import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';
import '../models/visit_record.dart';
import '../models/vehicle.dart';
import '../models/company.dart';
import '../models/neighborhood.dart';
import 'database_service.dart';

class OfflineSyncService {
  static const String _visitRecordsBoxName = 'visit_records';
  static const String _vehiclesBoxName = 'vehicles';
  static const String _companiesBoxName = 'companies';
  static const String _neighborhoodsBoxName = 'neighborhoods';
  static const String _syncQueueBoxName = 'sync_queue';
  
  final DatabaseService _databaseService;
  StreamSubscription? _connectivitySubscription;
  bool _isSyncing = false;
  
  // Boxes for offline storage
  late Box<String> _visitRecordsBox;
  late Box<String> _vehiclesBox;
  late Box<String> _companiesBox;
  late Box<String> _neighborhoodsBox;
  late Box<String> _syncQueueBox;
  
  OfflineSyncService(this._databaseService);
  
  // Initialize Hive and open boxes
  Future<void> initialize() async {
    await Hive.initFlutter();
    
    _visitRecordsBox = await Hive.openBox<String>(_visitRecordsBoxName);
    _vehiclesBox = await Hive.openBox<String>(_vehiclesBoxName);
    _companiesBox = await Hive.openBox<String>(_companiesBoxName);
    _neighborhoodsBox = await Hive.openBox<String>(_neighborhoodsBoxName);
    _syncQueueBox = await Hive.openBox<String>(_syncQueueBoxName);
    
    // Listen for connectivity changes
    _connectivitySubscription = Connectivity()
        .onConnectivityChanged
        .listen(_handleConnectivityChange);
        
    // Try to sync on startup if online
    final connectivityResult = await Connectivity().checkConnectivity();
    if (connectivityResult != ConnectivityResult.none) {
      syncOfflineRecords();
    }
  }
  
  // Save a visit record offline
  Future<void> saveVisitRecordOffline(VisitRecord record) async {
    try {
      // Generate a temporary local ID if none exists
      final localId = record.id ?? -DateTime.now().millisecondsSinceEpoch;
      
      // Create a copy of the record with the local ID
      final recordWithId = VisitRecord(
        id: localId,
        vehicleId: record.vehicleId,
        entryTime: record.entryTime,
        exitTime: record.exitTime,
        neighborhoodId: record.neighborhoodId,
        wasteType: record.wasteType,
        notes: record.notes,
        createdBy: record.createdBy,
        imageUrl: record.imageUrl,
        offlineCreated: true,
        syncStatus: 'Pending',
        licensePlate: record.licensePlate,
        companyName: record.companyName,
        neighborhoodName: record.neighborhoodName,
      );
      
      // Store the record as JSON string
      final recordJson = jsonEncode(recordWithId.toMap());
      await _visitRecordsBox.put(localId.toString(), recordJson);
      
      // Add to sync queue
      await _syncQueueBox.put(localId.toString(), 'visit_record');
      
      debugPrint('Saved visit record offline: $localId');
    } catch (e) {
      debugPrint('Error saving visit record offline: $e');
      throw Exception('Failed to save record offline: $e');
    }
  }
  
  // Save a vehicle offline
  Future<void> saveVehicleOffline(Vehicle vehicle) async {
    try {
      // Generate a temporary local ID if none exists
      final localId = vehicle.id ?? -DateTime.now().millisecondsSinceEpoch;
      
      // Create a copy of the vehicle with the local ID
      final vehicleWithId = Vehicle(
        id: localId,
        licensePlate: vehicle.licensePlate,
        companyId: vehicle.companyId,
        vehicleType: vehicle.vehicleType,
        vehicleImageUrl: vehicle.vehicleImageUrl,
        registrationDate: vehicle.registrationDate ?? DateTime.now(),
        isTemporary: vehicle.isTemporary,
        tempExpiryDate: vehicle.tempExpiryDate,
        companyName: vehicle.companyName,
        companyType: vehicle.companyType,
      );
      
      // Store the vehicle as JSON string
      final vehicleJson = jsonEncode(vehicleWithId.toMap());
      await _vehiclesBox.put(localId.toString(), vehicleJson);
      
      // Add to sync queue
      await _syncQueueBox.put(localId.toString(), 'vehicle');
      
      debugPrint('Saved vehicle offline: $localId');
      return;
    } catch (e) {
      debugPrint('Error saving vehicle offline: $e');
      throw Exception('Failed to save vehicle offline: $e');
    }
  }
  
  // Save a company offline
  Future<void> saveCompanyOffline(Company company) async {
    try {
      // Generate a temporary local ID if none exists
      final localId = company.id ?? -DateTime.now().millisecondsSinceEpoch;
      
      // Create a copy of the company with the local ID
      final companyWithId = Company(
        id: localId,
        name: company.name,
        type: company.type,
        contactPerson: company.contactPerson,
        contactNumber: company.contactNumber,
        email: company.email,
        registrationDate: company.registrationDate ?? DateTime.now(),
        status: company.status,
      );
      
      // Store the company as JSON string
      final companyJson = jsonEncode(companyWithId.toMap());
      await _companiesBox.put(localId.toString(), companyJson);
      
      // Add to sync queue
      await _syncQueueBox.put(localId.toString(), 'company');
      
      debugPrint('Saved company offline: $localId');
      return;
    } catch (e) {
      debugPrint('Error saving company offline: $e');
      throw Exception('Failed to save company offline: $e');
    }
  }
  
  // Save a neighborhood for offline search
  Future<void> saveNeighborhoodOffline(Neighborhood neighborhood) async {
    try {
      final id = neighborhood.id.toString();
      final neighborhoodJson = jsonEncode(neighborhood.toMap());
      await _neighborhoodsBox.put(id, neighborhoodJson);
      debugPrint('Saved neighborhood offline: $id');
    } catch (e) {
      debugPrint('Error saving neighborhood offline: $e');
    }
  }
  
  // Get offline visit records
  Future<List<VisitRecord>> getOfflineVisitRecords() async {
    final records = <VisitRecord>[];
    
    for (final key in _visitRecordsBox.keys) {
      try {
        final recordJson = _visitRecordsBox.get(key);
        if (recordJson != null) {
          final map = jsonDecode(recordJson) as Map<String, dynamic>;
          records.add(VisitRecord.fromMap(map));
        }
      } catch (e) {
        debugPrint('Error parsing visit record: $e');
      }
    }
    
    // Sort by entry time, newest first
    records.sort((a, b) => b.entryTime.compareTo(a.entryTime));
    return records;
  }
  
  // Search vehicles offline
  Future<List<Vehicle>> searchVehiclesOffline(String licensePlate) async {
    final vehicles = <Vehicle>[];
    
    for (final key in _vehiclesBox.keys) {
      try {
        final vehicleJson = _vehiclesBox.get(key);
        if (vehicleJson != null) {
          final map = jsonDecode(vehicleJson) as Map<String, dynamic>;
          final vehicle = Vehicle.fromMap(map);
          
          if (vehicle.licensePlate.contains(licensePlate.toUpperCase())) {
            vehicles.add(vehicle);
          }
        }
      } catch (e) {
        debugPrint('Error parsing vehicle: $e');
      }
    }
    
    return vehicles;
  }
  
  // Search neighborhoods offline
  Future<List<Neighborhood>> searchNeighborhoodsOffline(String query) async {
    final neighborhoods = <Neighborhood>[];
    
    for (final key in _neighborhoodsBox.keys) {
      try {
        final neighborhoodJson = _neighborhoodsBox.get(key);
        if (neighborhoodJson != null) {
          final map = jsonDecode(neighborhoodJson) as Map<String, dynamic>;
          final neighborhood = Neighborhood.fromMap(map);
          
          if (neighborhood.name.toLowerCase().contains(query.toLowerCase())) {
            neighborhoods.add(neighborhood);
          }
        }
      } catch (e) {
        debugPrint('Error parsing neighborhood: $e');
      }
    }
    
    // Sort alphabetically
    neighborhoods.sort((a, b) => a.name.compareTo(b.name));
    return neighborhoods;
  }
  
  // Sync offline records with the server
  Future<void> syncOfflineRecords() async {
    if (_isSyncing) return;
    
    _isSyncing = true;
    debugPrint('Starting sync of offline records...');
    
    try {
      final keys = _syncQueueBox.keys.toList();
      
      for (final key in keys) {
        final recordType = _syncQueueBox.get(key);
        if (recordType == null) continue;
        
        try {
          switch (recordType) {
            case 'company':
              await _syncCompany(key);
              break;
            case 'vehicle':
              await _syncVehicle(key);
              break;
            case 'visit_record':
              await _syncVisitRecord(key);
              break;
          }
          
          // Remove from sync queue after successful sync
          await _syncQueueBox.delete(key);
        } catch (e) {
          debugPrint('Error syncing record $key: $e');
          // Keep in sync queue to retry later
        }
      }
      
      debugPrint('Sync completed');
    } finally {
      _isSyncing = false;
    }
  }
  
  // Sync a company to the server
  Future<void> _syncCompany(String key) async {
    final companyJson = _companiesBox.get(key);
    if (companyJson == null) return;
    
    final map = jsonDecode(companyJson) as Map<String, dynamic>;
    final company = Company.fromMap(map);
    
    // Skip if already synced (has a positive ID)
    if (company.id != null && company.id! > 0) return;
    
    // Register the company on the server
    final serverId = await _databaseService.registerNewCompany(company);
    
    if (serverId > 0) {
      // Update local record with server ID
      final updatedCompany = Company(
        id: serverId,
        name: company.name,
        type: company.type,
        contactPerson: company.contactPerson,
        contactNumber: company.contactNumber,
        email: company.email,
        registrationDate: company.registrationDate,
        status: company.status,
      );
      
      await _companiesBox.put(serverId.toString(), jsonEncode(updatedCompany.toMap()));
      await _companiesBox.delete(key);
      
      debugPrint('Company synced: $key -> $serverId');
    }
  }
  
  // Sync a vehicle to the server
  Future<void> _syncVehicle(String key) async {
    final vehicleJson = _vehiclesBox.get(key);
    if (vehicleJson == null) return;
    
    final map = jsonDecode(vehicleJson) as Map<String, dynamic>;
    final vehicle = Vehicle.fromMap(map);
    
    // Skip if already synced (has a positive ID)
    if (vehicle.id != null && vehicle.id! > 0) return;
    
    // Ensure the company is synced first if it exists
    if (vehicle.companyId != null && vehicle.companyId! < 0) {
      final companyKey = vehicle.companyId.toString();
      await _syncCompany(companyKey);
      
      // Get updated company ID
      for (final companyKey in _companiesBox.keys) {
        final companyJson = _companiesBox.get(companyKey);
        if (companyJson == null) continue;
        
        final companyMap = jsonDecode(companyJson) as Map<String, dynamic>;
        final company = Company.fromMap(companyMap);
        
        if (company.name == vehicle.companyName) {
          // Update vehicle with correct company ID
          final updatedVehicle = Vehicle(
            id: vehicle.id,
            licensePlate: vehicle.licensePlate,
            companyId: company.id,
            vehicleType: vehicle.vehicleType,
            vehicleImageUrl: vehicle.vehicleImageUrl,
            registrationDate: vehicle.registrationDate,
            isTemporary: vehicle.isTemporary,
            tempExpiryDate: vehicle.tempExpiryDate,
            companyName: vehicle.companyName,
            companyType: vehicle.companyType,
          );
          
          await _vehiclesBox.put(key, jsonEncode(updatedVehicle.toMap()));
          break;
        }
      }
    }
    
    // Register the vehicle on the server
    final serverId = await _databaseService.registerNewVehicle(vehicle);
    
    if (serverId > 0) {
      // Update local record with server ID
      final updatedVehicle = Vehicle(
        id: serverId,
        licensePlate: vehicle.licensePlate,
        companyId: vehicle.companyId,
        vehicleType: vehicle.vehicleType,
        vehicleImageUrl: vehicle.vehicleImageUrl,
        registrationDate: vehicle.registrationDate,
        isTemporary: vehicle.isTemporary,
        tempExpiryDate: vehicle.tempExpiryDate,
        companyName: vehicle.companyName,
        companyType: vehicle.companyType,
      );
      
      await _vehiclesBox.put(serverId.toString(), jsonEncode(updatedVehicle.toMap()));
      await _vehiclesBox.delete(key);
      
      debugPrint('Vehicle synced: $key -> $serverId');
    }
  }
  
  // Sync a visit record to the server
  Future<void> _syncVisitRecord(String key) async {
    final recordJson = _visitRecordsBox.get(key);
    if (recordJson == null) return;
    
    final map = jsonDecode(recordJson) as Map<String, dynamic>;
    final record = VisitRecord.fromMap(map);
    
    // Skip if already synced (has a positive ID)
    if (record.id != null && record.id! > 0) return;
    
    // Ensure the vehicle is synced first if it has a negative ID
    if (record.vehicleId < 0) {
      final vehicleKey = record.vehicleId.toString();
      await _syncVehicle(vehicleKey);
      
      // Get updated vehicle ID
      for (final vehicleKey in _vehiclesBox.keys) {
        final vehicleJson = _vehiclesBox.get(vehicleKey);
        if (vehicleJson == null) continue;
        
        final vehicleMap = jsonDecode(vehicleJson) as Map<String, dynamic>;
        final vehicle = Vehicle.fromMap(vehicleMap);
        
        if (vehicle.licensePlate == record.licensePlate) {
          // Update visit record with correct vehicle ID
          final updatedRecord = VisitRecord(
            id: record.id,
            vehicleId: vehicle.id!,
            entryTime: record.entryTime,
            exitTime: record.exitTime,
            neighborhoodId: record.neighborhoodId,
            wasteType: record.wasteType,
            notes: record.notes,
            createdBy: record.createdBy,
            imageUrl: record.imageUrl,
            offlineCreated: true,
            syncStatus: 'Pending',
            licensePlate: record.licensePlate,
            companyName: record.companyName,
            neighborhoodName: record.neighborhoodName,
          );
          
          await _visitRecordsBox.put(key, jsonEncode(updatedRecord.toMap()));
          
          // Update record instance
          map['vehicle_id'] = vehicle.id;
          map['sync_status'] = 'Pending';
        }
      }
    }
    
    // Save the record to the server
    final serverId = await _databaseService.saveVisitRecord(record);
    
    if (serverId > 0) {
      // Update local record with server ID
      final updatedRecord = VisitRecord(
        id: serverId,
        vehicleId: record.vehicleId,
        entryTime: record.entryTime,
        exitTime: record.exitTime,
        neighborhoodId: record.neighborhoodId,
        wasteType: record.wasteType,
        notes: record.notes,
        createdBy: record.createdBy,
        imageUrl: record.imageUrl,
        offlineCreated: true,
        syncStatus: 'Synced',
        licensePlate: record.licensePlate,
        companyName: record.companyName,
        neighborhoodName: record.neighborhoodName,
      );
      
      await _visitRecordsBox.put(serverId.toString(), jsonEncode(updatedRecord.toMap()));
      await _visitRecordsBox.delete(key);
      
      debugPrint('Visit record synced: $key -> $serverId');
    }
  }
  
  // Handle connectivity changes
  void _handleConnectivityChange(ConnectivityResult result) {
    if (result != ConnectivityResult.none) {
      debugPrint('Connection restored. Starting sync...');
      syncOfflineRecords();
    } else {
      debugPrint('Connection lost. Sync will be attempted when connection is restored.');
    }
  }
  
  // Check if we're online
  Future<bool> isOnline() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }
  
  // Get sync status
  Future<Map<String, int>> getSyncStatus() async {
    final totalRecords = _syncQueueBox.length;
    final pendingVisitRecords = _syncQueueBox.values
        .where((type) => type == 'visit_record')
        .length;
    final pendingVehicles = _syncQueueBox.values
        .where((type) => type == 'vehicle')
        .length;
    final pendingCompanies = _syncQueueBox.values
        .where((type) => type == 'company')
        .length;
    
    return {
      'total': totalRecords,
      'visit_records': pendingVisitRecords,
      'vehicles': pendingVehicles,
      'companies': pendingCompanies,
    };
  }
  
  void dispose() {
    _connectivitySubscription?.cancel();
  }
}