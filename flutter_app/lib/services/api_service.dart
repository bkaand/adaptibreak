/// API Service for AdaptiBreak Backend Communication
/// Handles all HTTP requests to the FastAPI backend

import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';
  
  /// Check backend health status
  static Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      throw Exception('Backend returned status ${response.statusCode}');
    } catch (e) {
      throw Exception('Backend connection failed: $e');
    }
  }
  
  /// Start a new fatigue detection session
  static Future<SessionResponse> startSession() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/start'),
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return SessionResponse.fromJson(data);
      }
      throw Exception('Failed to start session: ${response.statusCode}');
    } catch (e) {
      throw Exception('Start session failed: $e');
    }
  }
  
  /// Get current fatigue detection status
  static Future<StatusResponse> getStatus() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/status'),
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return StatusResponse.fromJson(data);
      }
      throw Exception('Failed to get status: ${response.statusCode}');
    } catch (e) {
      throw Exception('Get status failed: $e');
    }
  }
  
  /// Stop the current session
  static Future<SessionResponse> stopSession() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/stop'),
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return SessionResponse.fromJson(data);
      }
      throw Exception('Failed to stop session: ${response.statusCode}');
    } catch (e) {
      throw Exception('Stop session failed: $e');
    }
  }
}

/// Session response model
class SessionResponse {
  final String status;
  final String message;
  
  SessionResponse({
    required this.status,
    required this.message,
  });
  
  factory SessionResponse.fromJson(Map<String, dynamic> json) {
    return SessionResponse(
      status: json['status'] as String,
      message: json['message'] as String,
    );
  }
}

/// Status response model
class StatusResponse {
  final double score;
  final double blinkRate;
  final int yawnCount;
  final double headTilt;
  final double headForward;
  final double sessionDuration;
  final bool isCalibrating;
  final double calibrationProgress;
  
  StatusResponse({
    required this.score,
    required this.blinkRate,
    required this.yawnCount,
    required this.headTilt,
    required this.headForward,
    required this.sessionDuration,
    required this.isCalibrating,
    required this.calibrationProgress,
  });
  
  factory StatusResponse.fromJson(Map<String, dynamic> json) {
    return StatusResponse(
      score: (json['score'] as num).toDouble(),
      blinkRate: (json['blink_rate'] as num).toDouble(),
      yawnCount: json['yawn_count'] as int,
      headTilt: (json['head_tilt'] as num).toDouble(),
      headForward: (json['head_forward'] as num).toDouble(),
      sessionDuration: (json['session_duration'] as num).toDouble(),
      isCalibrating: json['is_calibrating'] as bool,
      calibrationProgress: (json['calibration_progress'] as num).toDouble(),
    );
  }
}

