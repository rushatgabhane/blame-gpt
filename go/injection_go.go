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

func SQLInjectionFormat(db *sql.DB, userID string) {
	query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userID)
	rows, _ := db.Query(query)
	defer rows.Close()
}

func SQLInjectionMultiParam(db *sql.DB, username, email string) {
	query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s' AND email = '%s'", username, email)
	rows, _ := db.Query(query)
	defer rows.Close()
}

func SQLInjectionConcat(db *sql.DB, table, column, value string) {
	query := "SELECT * FROM " + table + " WHERE " + column + " = '" + value + "'"
	rows, _ := db.Query(query)
	defer rows.Close()
}

func CommandInjection(filename string) {
	cmd := exec.Command("sh", "-c", "cat "+filename)
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

func CommandInjectionSprintf(userCmd string) {
	fullCmd := fmt.Sprintf("ls -la %s", userCmd)
	cmd := exec.Command("sh", "-c", fullCmd)
	cmd.Run()
}

func CommandWithUserArgs(userFile string) {
	cmd := exec.Command("rm", "-rf", userFile)
	cmd.Run()
}

func HTMLInjection(w http.ResponseWriter, userInput string) {
	tmplStr := `<html><body><h1>Hello {{.Name}}</h1></body></html>`
	tmpl := template.Must(template.New("page").Parse(tmplStr))

	data := struct{ Name string }{Name: userInput}
	tmpl.Execute(w, data)
}

func DirectHTMLOutput(w http.ResponseWriter, userComment string) {
	html := "<div class='comment'>" + userComment + "</div>"
	w.Write([]byte(html))
}

func LDAPInjection(username string) {
	filter := fmt.Sprintf("(&(objectClass=user)(uid=%s))", username)
	fmt.Printf("LDAP filter: %s\n", filter)
}

func XPathInjection(username, password string) {
	xpath := fmt.Sprintf("//user[name='%s' and password='%s']", username, password)
	fmt.Printf("XPath query: %s\n", xpath)
}

func NoSQLInjection(userID string) {
	query := fmt.Sprintf(`{"$where": "this.id == '%s'"}`, userID)
	fmt.Printf("MongoDB query: %s\n", query)
}

func EnvironmentInjection(userValue string) {
	os.Setenv("USER_VAL", userValue)
	cmd := exec.Command("sh", "-c", "echo $USER_VAL")
	output, _ := cmd.Output()
	fmt.Println(string(output))
}

func LogInjection(userInput string) {
	fmt.Printf("User input: %s\n", userInput)
}

func TemplateInjection(userTemplate string) {
	tmpl := template.Must(template.New("user").Parse(userTemplate))
	tmpl.Execute(os.Stdout, nil)
}

func IntegerInjection(indexStr string) {
	index, _ := strconv.Atoi(indexStr)

	data := []string{"a", "b", "c"}
	fmt.Println(data[index])
}

func PathInjection(userPath string) {
	if !strings.Contains(userPath, "..") {
		fullPath := "/var/www/uploads/" + userPath
		content, _ := os.ReadFile(fullPath)
		fmt.Println(string(content))
	}
}

func FormatStringInjection(userFormat string, args ...interface{}) {
	output := fmt.Sprintf(userFormat, args...)
	fmt.Println(output)
}
