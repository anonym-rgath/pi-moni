import requests
import sys
from datetime import datetime
import json

class PiMonitorAPITester:
    def __init__(self, base_url="https://pi-dashboard-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, expected_fields=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json={}, headers=headers, timeout=10)

            success = response.status_code == expected_status
            response_data = {}
            
            if success:
                try:
                    response_data = response.json()
                    print(f"✅ Passed - Status: {response.status_code}")
                    
                    # Validate expected fields if provided
                    if expected_fields:
                        for field in expected_fields:
                            if field not in response_data:
                                print(f"⚠️  Warning: Expected field '{field}' not found in response")
                            else:
                                print(f"✓ Field '{field}' present")
                    
                    self.tests_passed += 1
                    
                except json.JSONDecodeError:
                    print(f"⚠️  Warning: Response is not valid JSON")
                    success = False
                    
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error response: {error_data}")
                except:
                    print(f"Error response: {response.text}")

            self.test_results.append({
                "test": name,
                "endpoint": endpoint,
                "status": "PASS" if success else "FAIL",
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "response_data": response_data if success else None
            })

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            self.test_results.append({
                "test": name,
                "endpoint": endpoint,
                "status": "FAIL",
                "error": str(e)
            })
            return False, {}

    def test_host_metrics(self):
        """Test /api/metrics/host endpoint"""
        expected_fields = ['timestamp', 'cpu', 'memory', 'load_average', 'temperature', 'uptime_hours', 'hostname']
        success, response = self.run_test(
            "Host Metrics API",
            "GET",
            "api/metrics/host",
            200,
            expected_fields
        )
        
        if success and response:
            # Validate host metrics structure
            cpu = response.get('cpu', {})
            memory = response.get('memory', {})
            load_avg = response.get('load_average', {})
            temp = response.get('temperature', {})
            
            print(f"  CPU Usage: {cpu.get('usage_percent', 'N/A')}%")
            print(f"  Memory Usage: {memory.get('usage_percent', 'N/A')}%")
            print(f"  Load Average (1min): {load_avg.get('1min', 'N/A')}")
            print(f"  Temperature: {temp.get('celsius', 'N/A')}°C")
            print(f"  Hostname: {response.get('hostname', 'N/A')}")
            
        return success

    def test_container_metrics(self):
        """Test /api/metrics/containers endpoint"""
        success, response = self.run_test(
            "Container Metrics API",
            "GET",
            "api/metrics/containers",
            200
        )
        
        if success and response:
            if isinstance(response, list):
                print(f"  Found {len(response)} containers")
                for container in response:
                    name = container.get('name', 'Unknown')
                    status = container.get('status', 'Unknown')
                    cpu_usage = container.get('cpu', {}).get('usage_percent', 0)
                    print(f"    - {name}: {status} (CPU: {cpu_usage}%)")
            else:
                print("  ⚠️  Expected array response")
                success = False
                
        return success

    def test_all_metrics(self):
        """Test /api/metrics/all endpoint"""
        expected_fields = ['host', 'containers']
        success, response = self.run_test(
            "All Metrics API",
            "GET",
            "api/metrics/all",
            200,
            expected_fields
        )
        
        if success and response:
            host_data = response.get('host', {})
            containers_data = response.get('containers', [])
            
            print(f"  Host data present: {'✓' if host_data else '✗'}")
            print(f"  Containers count: {len(containers_data) if isinstance(containers_data, list) else 'Invalid'}")
            
        return success

    def test_api_root(self):
        """Test /api/ root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "api/",
            200
        )
        return success

    def print_summary(self):
        """Print test summary"""
        print(f"\n" + "="*50)
        print(f"📊 TEST SUMMARY")
        print(f"="*50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed != self.tests_run:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result.get('error', 'Status code mismatch')}")

def main():
    print("🚀 Starting Pi Monitor API Tests")
    print("="*50)
    
    tester = PiMonitorAPITester()
    
    # Run all tests
    tests = [
        tester.test_api_root,
        tester.test_host_metrics,
        tester.test_container_metrics,
        tester.test_all_metrics
    ]
    
    for test in tests:
        test()
    
    tester.print_summary()
    
    # Return exit code based on results
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())