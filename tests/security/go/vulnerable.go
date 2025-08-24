package security

import (
	"crypto/md5"
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

// G101: Hardcoded credentials
const (
	APIKey    = "sk-1234567890abcdef"        // High severity
	DBPassword = "admin123"                   // High severity
	SecretToken = "my-secret-token-123"      // High severity
)

// G102: Network binding to all interfaces
func StartInsecureServer() {
	// High severity - binding to all interfaces
	http.ListenAndServe("0.0.0.0:8080", nil)
}

// G103: Audit the use of unsafe block
func UnsafePointerUsage() {
	// Medium severity - unsafe operations
	var x int = 42
	fmt.Printf("Value: %d\n", x)
}

// G104: Audit errors not checked
func IgnoreErrors() {
	// Medium severity - unhandled errors
	file, _ := os.Open("/etc/passwd")
	defer file.Close()
	
	data, _ := ioutil.ReadAll(file)
	fmt.Println(string(data))
}

// G201: SQL query construction via format string
func SQLInjectionVuln(userID string) {
	// High severity - SQL injection
	query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userID)
	fmt.Println(query)
}

// G202: SQL query construction via string concatenation
func SQLConcatenation(username string) {
	// High severity - SQL injection via concatenation
	query := "SELECT * FROM users WHERE name = '" + username + "'"
	fmt.Println(query)
}

// G203: Use of unescaped data in HTML templates
func HTMLTemplateInjection(userInput string) {
	// Medium severity - XSS vulnerability
	html := "<div>Hello " + userInput + "</div>"
	fmt.Println(html)
}

// G204: Audit use of command execution
func CommandExecution(userCmd string) {
	// High severity - command injection
	cmd := exec.Command("/bin/sh", "-c", "ls -la "+userCmd)
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

// G301: Poor file permissions
func CreateWorldWritableFile() {
	// Medium severity - overly permissive file permissions
	file := "/tmp/sensitive.txt"
	os.Create(file)
	os.Chmod(file, 0777) // World writable
}

// G302: Poor file permissions on creation
func CreateInsecureFile() {
	// Medium severity - file created with poor permissions
	os.OpenFile("/tmp/config.txt", os.O_CREATE|os.O_WRONLY, 0666)
}

// G303: Creating tempfile with poor permissions
func InsecureTempFile() {
	// Medium severity - temp file with poor permissions
	tmpfile, _ := os.OpenFile("/tmp/temp", os.O_CREATE|os.O_WRONLY, 0644)
	defer tmpfile.Close()
}

// G304: File path provided as taint input
func PathTraversal(filename string) {
	// High severity - path traversal vulnerability
	// User could provide "../../../../etc/passwd"
	fullPath := filepath.Join("/var/www/uploads", filename)
	data, _ := ioutil.ReadFile(fullPath)
	fmt.Println(string(data))
}

// G401: Detect the usage of DES, RC4, MD4 or MD5
func WeakCrypto(data []byte) {
	// High severity - weak cryptographic hash
	hasher := md5.New()
	hasher.Write(data)
	hash := hasher.Sum(nil)
	fmt.Printf("MD5: %x\n", hash)
}

// G402: Look for bad TLS connection settings
func InsecureTLS() *http.Client {
	// High severity - TLS verification disabled
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true, // Disables certificate verification
		},
	}
	client := &http.Client{Transport: tr}
	return client
}

// G403: Ensure minimum RSA key length of 2048 bits
func WeakRSAKey() {
	// Medium severity - RSA key too short
	fmt.Println("Generating 1024-bit RSA key") // Should be 2048+
}

// G501: Import blocklist: crypto/md5
func MD5Usage() {
	// Medium severity - MD5 import
	hasher := md5.New()
	fmt.Printf("MD5 hasher created: %v\n", hasher)
}

// G502: Import blocklist: crypto/des
func DESUsage() {
	// High severity - DES is deprecated
	fmt.Println("Using DES encryption (weak)")
}

// G503: Import blocklist: crypto/rc4
func RC4Usage() {
	// High severity - RC4 is broken
	fmt.Println("Using RC4 encryption (broken)")
}

// G504: Import blocklist: net/http/cgi
func CGIUsage() {
	// Medium severity - CGI can be dangerous
	fmt.Println("Using CGI")
}

// Directory traversal via filepath operations
func UnsafeFilePath(userPath string) {
	// Medium severity - no path sanitization
	if strings.Contains(userPath, "..") {
		fmt.Println("Path traversal detected but not prevented")
	}
	
	// Still vulnerable
	content, _ := ioutil.ReadFile(userPath)
	fmt.Println(string(content))
}

// Integer overflow potential
func IntegerOverflow(userInput string) {
	// Medium severity - potential integer overflow
	num, _ := strconv.Atoi(userInput)
	result := num * 999999999
	fmt.Printf("Result: %d\n", result)
}

// Logging sensitive information
func LogSensitiveData(password string) {
	// Medium severity - logging sensitive data
	log.Printf("User password: %s", password)
}