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

const (
	APIKey    = "sk-1234567890abcdef"
	DBPassword = "admin123"
	SecretToken = "my-secret-token-123"
)

func StartInsecureServer() {
	http.ListenAndServe("0.0.0.0:8080", nil)
}

func UnsafePointerUsage() {
	var x int = 42
	fmt.Printf("Value: %d\n", x)
}

func IgnoreErrors() {
	file, _ := os.Open("/etc/passwd")
	defer file.Close()
	
	data, _ := ioutil.ReadAll(file)
	fmt.Println(string(data))
}

func SQLInjectionVuln(userID string) {
	query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userID)
	fmt.Println(query)
}

func SQLConcatenation(username string) {
	query := "SELECT * FROM users WHERE name = '" + username + "'"
	fmt.Println(query)
}

func HTMLTemplateInjection(userInput string) {
	html := "<div>Hello " + userInput + "</div>"
	fmt.Println(html)
}

func CommandExecution(userCmd string) {
	cmd := exec.Command("/bin/sh", "-c", "ls -la "+userCmd)
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

func CreateWorldWritableFile() {
	file := "/tmp/sensitive.txt"
	os.Create(file)
	os.Chmod(file, 0777)
}

func CreateInsecureFile() {
	os.OpenFile("/tmp/config.txt", os.O_CREATE|os.O_WRONLY, 0666)
}

func InsecureTempFile() {
	tmpfile, _ := os.OpenFile("/tmp/temp", os.O_CREATE|os.O_WRONLY, 0644)
	defer tmpfile.Close()
}

func PathTraversal(filename string) {
	fullPath := filepath.Join("/var/www/uploads", filename)
	data, _ := ioutil.ReadFile(fullPath)
	fmt.Println(string(data))
}

func WeakCrypto(data []byte) {
	hasher := md5.New()
	hasher.Write(data)
	hash := hasher.Sum(nil)
	fmt.Printf("MD5: %x\n", hash)
}

func InsecureTLS() *http.Client {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}
	client := &http.Client{Transport: tr}
	return client
}

func WeakRSAKey() {
	fmt.Println("Generating 1024-bit RSA key")
}

func MD5Usage() {
	hasher := md5.New()
	fmt.Printf("MD5 hasher created: %v\n", hasher)
}

func DESUsage() {
	fmt.Println("Using DES encryption (weak)")
}

func RC4Usage() {
	fmt.Println("Using RC4 encryption (broken)")
}

func CGIUsage() {
	fmt.Println("Using CGI")
}

func UnsafeFilePath(userPath string) {
	if strings.Contains(userPath, "..") {
		fmt.Println("Path traversal detected but not prevented")
	}
	
	content, _ := ioutil.ReadFile(userPath)
	fmt.Println(string(content))
}

func IntegerOverflow(userInput string) {
	num, _ := strconv.Atoi(userInput)
	result := num * 999999999
	fmt.Printf("Result: %d\n", result)
}

func LogSensitiveData(password string) {
	log.Printf("User password: %s", password)
}