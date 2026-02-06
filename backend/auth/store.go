package auth

import (
	"database/sql"
	"fmt"

	"golang.org/x/crypto/bcrypt"
	_ "modernc.org/sqlite"
)

type Store struct {
	db *sql.DB
}

type User struct {
	ID       int64
	Username string
	Password string
}

func NewStore(dbPath string) (*Store, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}

	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		password TEXT NOT NULL
	)`)
	if err != nil {
		return nil, fmt.Errorf("create table: %w", err)
	}

	return &Store{db: db}, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) CreateUser(username, password string) error {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	_, err = s.db.Exec("INSERT INTO users (username, password) VALUES (?, ?)", username, string(hash))
	return err
}

func (s *Store) Authenticate(username, password string) (*User, error) {
	var u User
	err := s.db.QueryRow("SELECT id, username, password FROM users WHERE username = ?", username).
		Scan(&u.ID, &u.Username, &u.Password)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}
	if err := bcrypt.CompareHashAndPassword([]byte(u.Password), []byte(password)); err != nil {
		return nil, fmt.Errorf("invalid password")
	}
	return &u, nil
}

func (s *Store) UserExists(username string) bool {
	var count int
	s.db.QueryRow("SELECT COUNT(*) FROM users WHERE username = ?", username).Scan(&count)
	return count > 0
}

func (s *Store) EnsureDefaultUser(username, password string) error {
	if s.UserExists(username) {
		return nil
	}
	return s.CreateUser(username, password)
}
