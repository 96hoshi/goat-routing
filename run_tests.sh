#!/bin/bash
# filepath: /app/run_all_tests_and_generate_reports.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create necessary directories
print_step "Creating log dir..."
mkdir -p logs

# Function to run a command and log output
run_command() {
    local description="$1"
    local command="$2"
    local log_file="logs/${description// /_}.log"
    
    print_step "$description"
    echo "Command: $command" > "$log_file"
    echo "Started at: $(date)" >> "$log_file"
    echo "----------------------------------------" >> "$log_file"
    
    if eval "$command" >> "$log_file" 2>&1; then
        print_success "$description completed"
        return 0
    else
        print_error "$description failed (check $log_file)"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "🚀 Starting comprehensive routing test suite..."
    echo "=============================================="
    echo -e "${NC}"
    
    # Step: Run basic plausibility tests
    run_command "Running plausibility tests" \
        "python -m pytest tests/test_ab_routing_plausibility.py -v -s --tb=short"

    # Step: Run benchmark tests to create CSV files
    run_command "Running benchmark tests" \
        "python -m pytest tests/test_ab_routing_benchmarking.py -v -s --tb=short"
    
    # Step: Run modes comparison (generates comparison CSVs)
    run_command "Generating modes comparison data" \
        "python tests/scripts/modes_comparison.py"
    
    # Step: Generate visualizations 
    print_step "Generating visualization plots..."
    
    # Step: Generate routing comparisons
    run_command "Generating routing comparisons" \
        "python tests/scripts/visualize_routing_comparison.py"

    # Step: Visualize benchmark results
    run_command "Visualizing benchmark results" \
        "python tests/scripts/visualize_benchmark.py"
    
    # Step: Generate comprehensive report
    generate_report
    
    # Step: Show summary
    show_summary
}

# Function to generate a comprehensive report
generate_report() {
    print_step "Generating comprehensive report..."
    
    cat > tests/results/test_execution_report.md << EOF
# Routing Test Suite Execution Report

**Generated:** $(date)
**Execution Time:** Started at script launch

## Test Results Summary

### Files Generated:

#### CSV Data Files:
$(find tests/results -name "*.csv" -printf "- %f\n" 2>/dev/null || echo "- No CSV files found")

#### Image Files:
$(find tests/results/images -name "*.png" -printf "- %f\n" 2>/dev/null || echo "- No image files found")

#### Log Files:
$(find logs -name "*.log" -printf "- %f\n" 2>/dev/null || echo "- No log files found")

## Coordinate Sets Used:

### Aachen Coordinates (Local):
- $(grep -c "(" tests/coords/lists.py | head -1) coordinate pairs for local Aachen testing

### Mannheim Coordinates (Regional):
- $(grep -c "49\." tests/coords/lists.py) coordinate pairs for regional Mannheim testing

### Germany Coordinates (Long Distance):
- $(grep -c "52\.\|48\.\|50\.\|51\.\|53\." tests/coords/lists.py) coordinate pairs for long-distance German routes

## Services Tested:
- MOTIS (Public Transport)
- Google Maps (Public Transport & Driving)
- OpenTripPlanner (OTP) - if available
- Valhalla (Driving) - if available

## Generated Visualizations:
- Line plots for trend analysis
- Scatter plots for distribution analysis  
- Bar plots for service comparison
- Grouped bar plots for direct comparison

---
*This report was generated automatically by the test suite execution script.*
EOF
    
    print_success "Report generated: tests/results/test_execution_report.md"
}

# Function to show final summary
show_summary() {
    echo -e "${BLUE}"
    echo "📊 EXECUTION SUMMARY"
    echo "==================="
    echo -e "${NC}"
    
    echo "📁 Generated Files:"
    echo "   CSV Files: $(find tests/results -name "*.csv" 2>/dev/null | wc -l)"
    echo "   Image Files: $(find tests/results/images -name "*.png" 2>/dev/null | wc -l)" 
    echo "   Log Files: $(find logs -name "*.log" 2>/dev/null | wc -l)"
    
    echo ""
    echo "📂 Key Directories:"
    echo "   📊 CSV Results: tests/results/"
    echo "   🎨 Images: tests/results/images/"
    echo "   📋 Logs: logs/"
    
    echo ""
    echo "🔍 To view results:"
    echo "   ls -la tests/results/"
    echo "   ls -la tests/results/images/"
    
    print_success "All tests and report generation completed!"
}

# Execute main function
main "$@"