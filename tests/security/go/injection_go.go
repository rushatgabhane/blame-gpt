package security

import (
	"database/sql"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

// G201: SQL injection via format strings
func SQLInjectionFormat(db *sql.DB, userID string) {
	// High severity - SQL injection
	query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userID)
	rows, _ := db.Query(query)
	defer rows.Close()
}

// G201: SQL injection with multiple parameters
func SQLInjectionMultiParam(db *sql.DB, username, email string) {
	// High severity - SQL injection with multiple inputs
	query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s' AND email = '%s'", username, email)
	rows, _ := db.Query(query)
	defer rows.Close()
}

// G202: SQL injection via string concatenation
func SQLInjectionConcat(db *sql.DB, table, column, value string) {
	// High severity - dynamic query construction
	query := "SELECT * FROM " + table + " WHERE " + column + " = '" + value + "'"
	rows, _ := db.Query(query)
	defer rows.Close()
}

// G204: Command injection
func CommandInjection(filename string) {
	// High severity - command injection
	cmd := exec.Command("sh", "-c", "cat "+filename)
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

// G204: Command injection with fmt.Sprintf
func CommandInjectionSprintf(userCmd string) {
	// High severity - command injection via format string
	fullCmd := fmt.Sprintf("ls -la %s", userCmd)
	cmd := exec.Command("sh", "-c", fullCmd)
	cmd.Run()
}

// G204: Command injection with user-controlled arguments
func CommandWithUserArgs(userFile string) {
	// High severity - user controls command arguments
	cmd := exec.Command("rm", "-rf", userFile)
	cmd.Run()
}

// G203: HTML template without escaping
func HTMLInjection(w http.ResponseWriter, userInput string) {
	// Medium severity - XSS vulnerability
	tmplStr := `<html><body><h1>Hello {{.Name}}</h1></body></html>`
	tmpl := template.Must(template.New("page").Parse(tmplStr))

	data := struct{ Name string }{Name: userInput}
	tmpl.Execute(w, data)
}

// G203: Direct HTML output without escaping
func DirectHTMLOutput(w http.ResponseWriter, userComment string) {
	// Medium severity - XSS via direct output
	html := "<div class='comment'>" + userComment + "</div>"
	w.Write([]byte(html))
}

// LDAP injection
func LDAPInjection(username string) {
	// Medium severity - LDAP injection
	filter := fmt.Sprintf("(&(objectClass=user)(uid=%s))", username)
	fmt.Printf("LDAP filter: %s\n", filter)
}

// XPath injection
func XPathInjection(username, password string) {
	// Medium severity - XPath injection
	xpath := fmt.Sprintf("//user[name='%s' and password='%s']", username, password)
	fmt.Printf("XPath query: %s\n", xpath)
}

// NoSQL injection (MongoDB-style)
func NoSQLInjection(userID string) {
	// Medium severity - NoSQL injection
	query := fmt.Sprintf(`{"$where": "this.id == '%s'"}`, userID)
	fmt.Printf("MongoDB query: %s\n", query)
}

// OS command via environment variable
func EnvironmentInjection(userValue string) {
	// Medium severity - environment variable injection
	os.Setenv("USER_VAL", userValue)
	cmd := exec.Command("sh", "-c", "echo $USER_VAL")
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

// Log injection
func LogInjection(userInput string) {
	// Low-Medium severity - log injection can lead to log poisoning
	fmt.Printf("User input: %s\n", userInput)
	// If userInput contains newlines, it can inject fake log entries
}

// Template injection
func TemplateInjection(userTemplate string) {
	// High severity - template injection can lead to RCE
	tmpl := template.Must(template.New("user").Parse(userTemplate))
	tmpl.Execute(os.Stdout, nil)
}

// Integer injection leading to array bounds
func IntegerInjection(indexStr string) {
	// Medium severity - potential array bounds issue
	index, _ := strconv.Atoi(indexStr)

	data := []string{"a", "b", "c"}
	// No bounds checking - could panic or access invalid memory
	fmt.Println(data[index])
}

// Path injection
func PathInjection(userPath string) {
	// High severity - path traversal
	// User could provide "../../../etc/passwd"
	if !strings.Contains(userPath, "..") {
		// Weak validation - can be bypassed
		fullPath := "/var/www/uploads/" + userPath
		content, _ := os.ReadFile(fullPath)
		fmt.Println(string(content))
	}
}

// Format string injection
func FormatStringInjection(userFormat string, args ...interface{}) {
	// Medium severity - format string vulnerability
	output := fmt.Sprintf(userFormat, args...)
	fmt.Println(output)
}
