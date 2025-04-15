import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  
  // Get current user
  User? get currentUser => _auth.currentUser;
  
  // Auth state changes stream
  Stream<User?> get authStateChanges => _auth.authStateChanges();
  
  // Sign in with email and password
  Future<User?> signInWithEmailAndPassword(String email, String password) async {
    try {
      final userCredential = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Store credentials for offline login
      await _saveCredentials(email, password);
      
      return userCredential.user;
    } catch (e) {
      debugPrint('Error signing in: $e');
      throw Exception('Failed to sign in: ${e.toString()}');
    }
  }
  
  // Sign in with Google
  Future<User?> signInWithGoogle() async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;
      
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );
      
      final userCredential = await _auth.signInWithCredential(credential);
      return userCredential.user;
    } catch (e) {
      debugPrint('Error signing in with Google: $e');
      throw Exception('Failed to sign in with Google: ${e.toString()}');
    }
  }
  
  // Register with email and password
  Future<User?> registerWithEmailAndPassword(String email, String password) async {
    try {
      final userCredential = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Store credentials for offline login
      await _saveCredentials(email, password);
      
      return userCredential.user;
    } catch (e) {
      debugPrint('Error registering: $e');
      throw Exception('Failed to register: ${e.toString()}');
    }
  }
  
  // Sign out
  Future<void> signOut() async {
    try {
      await _auth.signOut();
      await _googleSignIn.signOut();
      
      // Clear stored credentials
      await _clearCredentials();
    } catch (e) {
      debugPrint('Error signing out: $e');
      throw Exception('Failed to sign out: ${e.toString()}');
    }
  }
  
  // Offline login
  Future<bool> offlineLogin(String email, String password) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final storedEmail = prefs.getString('auth_email');
      final storedPassword = prefs.getString('auth_password');
      
      if (storedEmail == email && storedPassword == password) {
        return true;
      }
      
      return false;
    } catch (e) {
      debugPrint('Error with offline login: $e');
      return false;
    }
  }
  
  // Check if offline login is available
  Future<bool> isOfflineLoginAvailable() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final storedEmail = prefs.getString('auth_email');
      final storedPassword = prefs.getString('auth_password');
      
      return storedEmail != null && storedPassword != null;
    } catch (e) {
      debugPrint('Error checking offline login: $e');
      return false;
    }
  }
  
  // Save credentials for offline login
  Future<void> _saveCredentials(String email, String password) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_email', email);
      await prefs.setString('auth_password', password);
    } catch (e) {
      debugPrint('Error saving credentials: $e');
    }
  }
  
  // Clear stored credentials
  Future<void> _clearCredentials() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('auth_email');
      await prefs.remove('auth_password');
    } catch (e) {
      debugPrint('Error clearing credentials: $e');
    }
  }
  
  // Send password reset email
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } catch (e) {
      debugPrint('Error sending password reset email: $e');
      throw Exception('Failed to send password reset email: ${e.toString()}');
    }
  }
}