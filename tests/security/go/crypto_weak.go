package security

import (
	"crypto/des"
	"crypto/md5"
	"crypto/rc4"
	"crypto/sha1"
	"fmt"
	"math/rand"
	"time"
)

// G401: Weak cryptographic primitives
func WeakHashFunctions(data []byte) {
	// High severity - MD5
	md5Hash := md5.Sum(data)
	fmt.Printf("MD5: %x\n", md5Hash)

	// High severity - SHA1
	sha1Hash := sha1.Sum(data)
	fmt.Printf("SHA1: %x\n", sha1Hash)
}

// G401: DES encryption (broken)
func DESEncryption(plaintext []byte) {
	// High severity - DES is cryptographically broken
	key := []byte("12345678") // 8-byte DES key

	block, err := des.NewCipher(key)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	// This is vulnerable
	ciphertext := make([]byte, len(plaintext))
	block.Encrypt(ciphertext, plaintext)
	fmt.Printf("DES Encrypted: %x\n", ciphertext)
}

// G402: RC4 stream cipher (broken)
func RC4Encryption(plaintext []byte) {
	// High severity - RC4 is cryptographically broken
	key := []byte("secret-key")

	cipher, err := rc4.NewCipher(key)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	ciphertext := make([]byte, len(plaintext))
	cipher.XORKeyStream(ciphertext, plaintext)
	fmt.Printf("RC4 Encrypted: %x\n", ciphertext)
}

// G404: Weak random number generation
func WeakRandomness() {
	// Medium severity - predictable random numbers
	rand.Seed(time.Now().Unix())

	// Generate session token with weak randomness
	sessionToken := rand.Int63()
	fmt.Printf("Session token: %d\n", sessionToken)

	// Generate password with math/rand (predictable)
	password := make([]byte, 16)
	for i := range password {
		password[i] = byte(rand.Intn(256))
	}
	fmt.Printf("Generated password: %x\n", password)
}

// G501: Blacklisted import usage
func BlacklistedImports() {
	// Medium severity - using blacklisted crypto packages
	fmt.Println("Using weak crypto imports")

	// This function imports md5, des, rc4 which are blacklisted
	data := []byte("sensitive data")

	// MD5 usage
	hasher := md5.New()
	hasher.Write(data)

	// This demonstrates the import-based detection
}

// ECB mode usage (if available)
func ECBMode(data []byte) {
	// Medium severity - ECB mode is insecure
	key := []byte("16-byte-aes-key!")

	// Note: Go's crypto package doesn't expose ECB directly,
	// but this demonstrates the concept
	fmt.Printf("Would use ECB mode with key: %x\n", key)
	fmt.Printf("ECB mode is deterministic and reveals patterns\n")
}

// Hardcoded cryptographic keys
func HardcodedKeys() {
	// High severity - hardcoded encryption keys
	const (
		AESKey    = "my-32-byte-aes-key-for-encryption!"
		HMACKey   = "my-hmac-secret-key"
		JWTSecret = "jwt-signing-secret-key-123"
	)

	fmt.Printf("AES Key: %s\n", AESKey)
	fmt.Printf("HMAC Key: %s\n", HMACKey)
	fmt.Printf("JWT Secret: %s\n", JWTSecret)
}

// Weak key derivation
func WeakKeyDerivation(password string, salt []byte) {
	// Medium severity - weak key derivation
	// Using simple hash instead of proper PBKDF2/scrypt/argon2

	combined := append([]byte(password), salt...)
	key := md5.Sum(combined)

	fmt.Printf("Derived key: %x\n", key)
}

func CustomCrypto(data []byte) {
	encrypted := make([]byte, len(data))

	// Terrible "encryption" - XOR with predictable pattern
	for i, b := range data {
		encrypted[i] = b ^ byte(i%256)
	}

	fmt.Printf("Custom encrypted: %x\n", encrypted)
}

func ReusedNonce() {
	// Medium severity - IV/nonce reuse
	const fixedIV = "1234567890123456"

	fmt.Printf("Using fixed IV: %s\n", fixedIV)
	fmt.Println("This breaks semantic security")
}
