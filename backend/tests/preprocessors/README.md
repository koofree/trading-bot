# Preprocessor Tests - Quick Reference (unittest)

## Running Tests in Terminal

### Quick Commands (unittest)
```bash
# Run all preprocessor tests
python -m unittest discover tests/preprocessors/

# Run specific test file
python -m unittest tests.preprocessors.test_candlestick

# Run specific test class
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor

# Run specific test method
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor.test_hammer_detection

# With verbose output (add -v flag)
python -m unittest discover tests/preprocessors/ -v
python -m unittest tests.preprocessors.test_candlestick -v

# Run multiple test files
python -m unittest tests.preprocessors.test_candlestick tests.preprocessors.test_volume -v

# Run test file directly
python tests/preprocessors/test_candlestick.py
python tests/preprocessors/test_candlestick.py -v
```

### Test Files Overview
- `test_candlestick.py` - Candlestick pattern recognition tests (11 tests)
- `test_volume.py` - Volume analysis and indicators tests (17 tests)
- `test_price_action.py` - Price action and breakout tests (12 tests)
- `test_trend.py` - Trend analysis and moving average tests (13 tests)
- `test_volatility.py` - Volatility measurement and Bollinger Bands tests (13 tests)
- `test_factory.py` - Factory pattern and orchestrator tests (17 tests)
- `test_integration.py` - Multi-processor integration tests (10 tests)

## Examples by Test Module

### Candlestick Tests
```bash
# Run all candlestick tests
python -m unittest tests.preprocessors.test_candlestick -v

# Test specific pattern detection
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor.test_hammer_detection
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor.test_doji_detection
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor.test_engulfing_detection
```

### Volume Tests
```bash
# Run all volume tests
python -m unittest tests.preprocessors.test_volume -v

# Test specific volume analysis
python -m unittest tests.preprocessors.test_volume.TestVolumeProcessor.test_volume_spike_detection
python -m unittest tests.preprocessors.test_volume.TestVolumeProcessor.test_accumulation_detection
```

### Factory and Orchestrator Tests
```bash
# Run all factory tests
python -m unittest tests.preprocessors.test_factory -v

# Test specific components
python -m unittest tests.preprocessors.test_factory.TestPreprocessorRegistry -v
python -m unittest tests.preprocessors.test_factory.TestPreprocessorFactory -v
python -m unittest tests.preprocessors.test_factory.TestPreprocessorOrchestrator -v
```

### Integration Tests
```bash
# Run all integration tests
python -m unittest tests.preprocessors.test_integration -v

# Test specific integration scenarios
python -m unittest tests.preprocessors.test_integration.TestPreprocessorIntegration.test_bull_market_consensus
python -m unittest tests.preprocessors.test_integration.TestPreprocessorIntegration.test_bear_market_consensus
```

## VSCode Usage

### Setup
1. Install Python extension by Microsoft
2. VSCode will auto-detect unittest configuration
3. Or manually configure: `Cmd+Shift+P` → "Python: Configure Tests" → Select "unittest" → Select "tests" folder

### Running Tests in VSCode
1. **Test Explorer**: 
   - Click Testing icon in sidebar (flask/beaker icon)
   - Navigate to tests/preprocessors/
   - Click play button next to test files/classes/methods

2. **From Editor**: 
   - Open any test file
   - Click "Run Test | Debug Test" above test methods

3. **Command Palette** (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows/Linux):
   - "Python: Run All Tests"
   - "Python: Run Current Test File"
   - "Test: Run Tests at Cursor"

4. **Tasks** (`Cmd+Shift+P` → "Tasks: Run Task"):
   - Run All Preprocessor Tests
   - Run Candlestick Tests
   - Run Volume Tests
   - Run Integration Tests

### Debugging Tests in VSCode
1. Set breakpoints by clicking left of line numbers
2. Click "Debug Test" above test method
3. Or use F5 with launch configurations:
   - Debug Current Test File
   - Debug All Preprocessor Tests
   - Debug Specific Test Method

## Test Status
- ✅ `test_candlestick.py` - 11/11 tests passing
- ✅ `test_volume.py` - 16/17 tests passing
- ⚠️ `test_price_action.py` - Needs processor implementation
- ⚠️ `test_trend.py` - Needs processor implementation  
- ⚠️ `test_volatility.py` - Needs processor implementation
- ✅ `test_factory.py` - Mostly passing
- ✅ `test_integration.py` - Mostly passing

## Common Patterns

### Running Working Tests Only
```bash
# Run tests that are currently passing
python -m unittest tests.preprocessors.test_candlestick tests.preprocessors.test_volume -v

# Run just candlestick tests
python -m unittest tests.preprocessors.test_candlestick -v

# Run factory and integration tests
python -m unittest tests.preprocessors.test_factory tests.preprocessors.test_integration -v
```

### Development Workflow
```bash
# 1. Run specific test while developing
python -m unittest tests.preprocessors.test_candlestick.TestCandlestickProcessor.test_hammer_detection -v

# 2. Run all tests for the module you're working on
python -m unittest tests.preprocessors.test_candlestick -v

# 3. Run all preprocessor tests to verify nothing broke
python -m unittest discover tests/preprocessors/ -v

# 4. Run the test file directly for quick feedback
python tests/preprocessors/test_candlestick.py
```

## Tips
- Add `-v` for verbose output to see which tests pass/fail
- Add `-f` for fail-fast (stop on first failure)
- Add `-b` to suppress output during passing tests
- Use `-k pattern` to run tests matching a pattern (requires unittest2 or pytest)
- Direct file execution (`python test_file.py`) works if file has `if __name__ == "__main__": unittest.main()`

## Running Original Test File
The original combined test file still exists and can be run:
```bash
# Run original test_preprocessors.py
python -m tests.test_preprocessors

# Or directly
python tests/test_preprocessors.py
```