import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize window manager
  await windowManager.ensureInitialized();
  
  WindowOptions windowOptions = const WindowOptions(
    size: Size(800, 600),
    center: true,
    backgroundColor: Colors.transparent,
    skipTaskbar: false,
    titleBarStyle: TitleBarStyle.normal,
    title: 'AdaptiBreak',
  );
  
  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });
  
  runApp(const AdaptiBreakApp());
}

class AdaptiBreakApp extends StatelessWidget {
  const AdaptiBreakApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AdaptiBreak',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4287f5),
          brightness: Brightness.light,
        ),
        cardTheme: CardThemeData(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(fontSize: 16),
          ),
        ),
      ),
      home: const MainWindow(),
    );
  }
}

class MainWindow extends StatefulWidget {
  const MainWindow({Key? key}) : super(key: key);

  @override
  State<MainWindow> createState() => _MainWindowState();
}

class _MainWindowState extends State<MainWindow> {
  static const String apiUrl = 'http://127.0.0.1:8000';
  
  bool isSessionActive = false;
  double fatigueScore = 0.0;
  double blinkRate = 0.0;
  int yawnCount = 0;
  double sessionDuration = 0.0;
  bool isCalibrating = false;
  double calibrationProgress = 0.0;
  
  Timer? statusTimer;
  
  List<double> fatigueHistory = [];
  
  @override
  void initState() {
    super.initState();
    checkBackendHealth();
  }
  
  @override
  void dispose() {
    statusTimer?.cancel();
    super.dispose();
  }
  
  // Project root path
  static const String projectRoot = '/Users/kaan/Desktop/adaptibreak-1';
  
  Future<void> launchFloatingBar() async {
    try {
      print('[INFO] Launching floating bar...');
      
      // Use 'open' to run the start script which handles everything
      await Process.run(
        'open',
        ['-a', 'Terminal', '$projectRoot/start_floating_bar.sh'],
      );
    } catch (e) {
      print('[ERROR] Could not launch floating bar: $e');
    }
  }
  
  Future<void> checkBackendHealth() async {
    try {
      final response = await http.get(Uri.parse('$apiUrl/health'));
      if (response.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Backend connected'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 2),
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backend not available: $e'),
            backgroundColor: Colors.orange,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }
  
  Future<void> startSession() async {
    try {
      final response = await http.post(Uri.parse('$apiUrl/start'));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['status'] == 'started' || data['status'] == 'already_running') {
          setState(() {
            isSessionActive = true;
            fatigueHistory.clear();
          });
          
          // Start polling status
          statusTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
            updateStatus();
          });
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Session started'),
                backgroundColor: Colors.green,
              ),
            );
            
            // Launch floating bar (which also launches camera preview)
            launchFloatingBar();
          }
        } else {
          throw Exception(data['message']);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
  
  Future<void> stopSession() async {
    try {
      final response = await http.post(Uri.parse('$apiUrl/stop'));
      
      if (response.statusCode == 200) {
        setState(() {
          isSessionActive = false;
          fatigueScore = 0.0;
          blinkRate = 0.0;
          yawnCount = 0;
          sessionDuration = 0.0;
          isCalibrating = false;
          calibrationProgress = 0.0;
        });
        
        statusTimer?.cancel();
        statusTimer = null;
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Session stopped'),
              backgroundColor: Colors.grey,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
  
  Future<void> updateStatus() async {
    if (!isSessionActive) return;
    
    try {
      final response = await http.get(Uri.parse('$apiUrl/status'));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        setState(() {
          fatigueScore = data['score']?.toDouble() ?? 0.0;
          blinkRate = data['blink_rate']?.toDouble() ?? 0.0;
          yawnCount = data['yawn_count'] ?? 0;
          sessionDuration = data['session_duration']?.toDouble() ?? 0.0;
          isCalibrating = data['is_calibrating'] ?? false;
          calibrationProgress = data['calibration_progress']?.toDouble() ?? 0.0;
          
          // Store history for chart (keep last 60 readings)
          fatigueHistory.add(fatigueScore);
          if (fatigueHistory.length > 60) {
            fatigueHistory.removeAt(0);
          }
        });
      }
    } catch (e) {
      // Silently fail - backend might be restarting
    }
  }
  
  String formatDuration(double seconds) {
    int minutes = (seconds / 60).floor();
    int secs = (seconds % 60).floor();
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: Center(
        child: SingleChildScrollView(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 700),
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
              // Header
              const Text(
                'AdaptiBreak',
                style: TextStyle(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2C3E50),
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Adaptive Study Break Assistant',
                style: TextStyle(
                  fontSize: 18,
                  color: Color(0xFF7F8C8D),
                  letterSpacing: 0.5,
                ),
              ),
              
              const SizedBox(height: 32),
              
              // Main card
              Card(
                elevation: 4,
                child: Container(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      // Status indicator
                      if (isSessionActive) ...[
                        if (isCalibrating) ...[
                          const Icon(
                            Icons.settings_suggest,
                            size: 48,
                            color: Colors.orange,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            'Calibrating... ${(calibrationProgress * 100).toInt()}%',
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.orange,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Please sit naturally for a few moments',
                            style: TextStyle(
                              fontSize: 14,
                              color: Color(0xFF7F8C8D),
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          const SizedBox(height: 20),
                          LinearProgressIndicator(
                            value: calibrationProgress,
                            backgroundColor: Colors.grey[200],
                            color: Colors.orange,
                            minHeight: 8,
                          ),
                        ] else ...[
                          const Icon(
                            Icons.visibility,
                            size: 48,
                            color: Color(0xFF4287f5),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Monitoring Active',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF4287f5),
                            ),
                          ),
                        ],
                        
                        const SizedBox(height: 30),
                        
                        // Metrics grid
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _buildMetricItem(
                              'Fatigue',
                              fatigueScore.toStringAsFixed(2),
                              Icons.psychology,
                              _getFatigueColor(fatigueScore),
                            ),
                            _buildMetricItem(
                              'Duration',
                              formatDuration(sessionDuration),
                              Icons.timer,
                              Colors.blue,
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 20),
                        
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _buildMetricItem(
                              'Blink Rate',
                              '${blinkRate.toStringAsFixed(1)}/min',
                              Icons.remove_red_eye,
                              Colors.purple,
                            ),
                            _buildMetricItem(
                              'Yawns',
                              yawnCount.toString(),
                              Icons.face,
                              Colors.orange,
                            ),
                          ],
                        ),
                      ] else ...[
                        const Icon(
                          Icons.play_circle_outline,
                          size: 64,
                          color: Color(0xFFBDC3C7),
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          'No Active Session',
                          style: TextStyle(
                            fontSize: 20,
                            color: Color(0xFF7F8C8D),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Click "Start Session" to begin monitoring',
                          style: TextStyle(
                            fontSize: 14,
                            color: Color(0xFF95A5A6),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Control buttons
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (!isSessionActive) ...[
                    ElevatedButton.icon(
                      onPressed: startSession,
                      icon: const Icon(Icons.play_arrow),
                      label: const Text('Start Session'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF4287f5),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 40,
                          vertical: 20,
                        ),
                      ),
                    ),
                  ] else ...[
                    OutlinedButton.icon(
                      onPressed: stopSession,
                      icon: const Icon(Icons.stop),
                      label: const Text('Stop Session'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 40,
                          vertical: 20,
                        ),
                        side: const BorderSide(
                          color: Color(0xFFE74C3C),
                          width: 2,
                        ),
                        foregroundColor: const Color(0xFFE74C3C),
                      ),
                    ),
                  ],
                ],
              ),
              
              const SizedBox(height: 24),
              
              // Footer info
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFECF0F1)),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: Color(0xFF3498DB),
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Fully offline • Local processing • No data stored',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey[600],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        ),
      ),
    );
  }
  
  Widget _buildMetricItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Color(0xFF95A5A6),
          ),
        ),
      ],
    );
  }
  
  Color _getFatigueColor(double score) {
    if (score > 0.6) return Colors.red;
    if (score > 0.4) return Colors.orange;
    return Colors.green;
  }
}

