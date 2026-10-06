import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('EX REVIVAL app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ExRevivalApp());
    // Pump past the 2s timer in splash screen
    await tester.pump(const Duration(milliseconds: 2500));
    expect(find.text('EX REVIVAL'), findsWidgets);
  });
}
