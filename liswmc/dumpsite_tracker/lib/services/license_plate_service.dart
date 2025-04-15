import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'package:uuid/uuid.dart';

class LicensePlateService {
  final textRecognizer = TextRecognizer();
  final ImagePicker _picker = ImagePicker();
  
  // Regular expression for Zambian license plates
  // Formats supported:
  // - ABC 1234 (standard format)
  // - AB 1234 A (older format)
  // - GRZ 123A (government vehicles)
  // - CD 12 (diplomatic vehicles)
  final RegExp _licensePlateRegex = RegExp(
    r'([A-Z]{2,3})\s*(\d{2,4})(?:\s*([A-Z]{1}))?',
    caseSensitive: false
  );
  
  // Take a photo using the camera
  Future<File?> takePhoto() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.rear,
        imageQuality: 100,
      );
      
      if (image == null) return null;
      
      return File(image.path);
    } catch (e) {
      debugPrint('Error taking photo: $e');
      return null;
    }
  }
  
  // Process the image to recognize license plate
  Future<String?> recognizeLicensePlate(File imageFile) async {
    try {
      final inputImage = InputImage.fromFile(imageFile);
      final recognizedText = await textRecognizer.processImage(inputImage);
      
      // Process text to extract license plate
      return _extractLicensePlate(recognizedText.text);
    } catch (e) {
      debugPrint('Error recognizing license plate: $e');
      return null;
    }
  }
  
  // Extract license plate from recognized text
  String? _extractLicensePlate(String text) {
    // Replace common OCR errors
    text = text.replaceAll('0', 'O')
               .replaceAll('1', 'I')
               .toUpperCase();
    
    // Split text into lines and process each line
    final lines = text.split('\n');
    
    for (final line in lines) {
      final match = _licensePlateRegex.firstMatch(line);
      if (match != null) {
        final letters = match.group(1) ?? '';
        final numbers = match.group(2) ?? '';
        final suffix = match.group(3) ?? '';
        
        // Format the license plate consistently
        if (suffix.isNotEmpty) {
          return '$letters $numbers $suffix';
        } else {
          return '$letters $numbers';
        }
      }
    }
    
    return null; // No license plate found
  }
  
  // Save the image to local storage and get the path
  Future<String> saveImage(File imageFile) async {
    final directory = await getApplicationDocumentsDirectory();
    final imagesDir = Directory('${directory.path}/vehicle_images');
    
    // Create directory if it doesn't exist
    if (!await imagesDir.exists()) {
      await imagesDir.create(recursive: true);
    }
    
    // Generate unique filename
    final uuid = Uuid();
    final fileName = '${uuid.v4()}.jpg';
    final savedImagePath = path.join(imagesDir.path, fileName);
    
    // Copy the image file
    await imageFile.copy(savedImagePath);
    
    return savedImagePath;
  }
  
  void dispose() {
    textRecognizer.close();
  }
}