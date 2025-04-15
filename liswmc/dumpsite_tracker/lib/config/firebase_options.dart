import 'package:firebase_core/firebase_core.dart';

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    // Firebase configuration for agripredict-82e4a project
    return const FirebaseOptions(
      apiKey: "AIzaSyAPIKEY", // You'll need to replace this with your actual Firebase API key
      appId: "1:APPID", // Replace with your actual Firebase App ID
      messagingSenderId: "SENDERID", // Replace with your actual Messaging Sender ID 
      projectId: "agripredict-82e4a",
    );
  }
}