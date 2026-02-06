package auth

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	store          *Store
	jwtSecret      string
	accessPassword string
}

func NewHandler(store *Store, jwtSecret, accessPassword string) *Handler {
	return &Handler{store: store, jwtSecret: jwtSecret, accessPassword: accessPassword}
}

type loginRequest struct {
	Type     string `json:"type"`
	Password string `json:"password,omitempty"`
	Username string `json:"username,omitempty"`
}

type authResponse struct {
	Token    string `json:"token"`
	Username string `json:"username"`
}

func (h *Handler) Login(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}

	switch req.Type {
	case "password":
		if req.Password != h.accessPassword {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid password"})
			return
		}
		token, err := GenerateToken(h.jwtSecret, "guest")
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "token generation failed"})
			return
		}
		c.JSON(http.StatusOK, authResponse{Token: token, Username: "guest"})

	case "account":
		user, err := h.store.Authenticate(req.Username, req.Password)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
			return
		}
		token, err := GenerateToken(h.jwtSecret, user.Username)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "token generation failed"})
			return
		}
		c.JSON(http.StatusOK, authResponse{Token: token, Username: user.Username})

	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid login type"})
	}
}

type registerRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func (h *Handler) Register(c *gin.Context) {
	var req registerRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	if len(req.Username) < 3 || len(req.Password) < 6 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "username min 3 chars, password min 6 chars"})
		return
	}
	if h.store.UserExists(req.Username) {
		c.JSON(http.StatusConflict, gin.H{"error": "username already exists"})
		return
	}
	if err := h.store.CreateUser(req.Username, req.Password); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create user"})
		return
	}
	token, err := GenerateToken(h.jwtSecret, req.Username)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "token generation failed"})
		return
	}
	c.JSON(http.StatusCreated, authResponse{Token: token, Username: req.Username})
}

func (h *Handler) JWTSecret() string {
	return h.jwtSecret
}
