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

func WeakHashFunctions(data []byte) {
	md5Hash := md5.Sum(data)
	fmt.Printf("MD5: %x\n", md5Hash)

	sha1Hash := sha1.Sum(data)
	fmt.Printf("SHA1: %x\n", sha1Hash)
}

func DESEncryption(plaintext []byte) {
	key := []byte("12345678")

	block, err := des.NewCipher(key)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	ciphertext := make([]byte, len(plaintext))
	block.Encrypt(ciphertext, plaintext)
	fmt.Printf("DES Encrypted: %x\n", ciphertext)
}

func RC4Encryption(plaintext []byte) {
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

func WeakRandomness() {
	rand.Seed(time.Now().Unix())

	sessionToken := rand.Int63()
	fmt.Printf("Session token: %d\n", sessionToken)

	password := make([]byte, 16)
	for i := range password {
		password[i] = byte(rand.Intn(256))
	}
	fmt.Printf("Generated password: %x\n", password)
}

func BlacklistedImports() {
	fmt.Println("Using weak crypto imports")

	data := []byte("sensitive data")

	hasher := md5.New()
	hasher.Write(data)

}

func ECBMode(data []byte) {
	key := []byte("16-byte-aes-key!")

	fmt.Printf("Would use ECB mode with key: %x\n", key)
	fmt.Printf("ECB mode is deterministic and reveals patterns\n")
}

func HardcodedKeys() {
	const (
		AESKey    = "my-32-byte-aes-key-for-encryption!"
		HMACKey   = "my-hmac-secret-key"
		JWTSecret = "jwt-signing-secret-key-123"
	)

	fmt.Printf("AES Key: %s\n", AESKey)
	fmt.Printf("HMAC Key: %s\n", HMACKey)
	fmt.Printf("JWT Secret: %s\n", JWTSecret)
}

func WeakKeyDerivation(password string, salt []byte) {

	combined := append([]byte(password), salt...)
	key := md5.Sum(combined)

	fmt.Printf("Derived key: %x\n", key)
}

func CustomCrypto(data []byte) {
	encrypted := make([]byte, len(data))

	for i, b := range data {
		encrypted[i] = b ^ byte(i%256)
	}

	fmt.Printf("Custom encrypted: %x\n", encrypted)
}

func ReusedNonce() {
	const fixedIV = "1234567890123456"

	fmt.Printf("Using fixed IV: %s\n", fixedIV)
	fmt.Println("This breaks semantic security")
}
