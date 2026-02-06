package proxy

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type APIHandler struct {
	manager *Manager
}

func NewAPIHandler(manager *Manager) *APIHandler {
	return &APIHandler{manager: manager}
}

func (h *APIHandler) GetRules(c *gin.Context) {
	c.JSON(http.StatusOK, h.manager.GetRules())
}

func (h *APIHandler) AddRule(c *gin.Context) {
	var req struct {
		PathPrefix string `json:"pathPrefix"`
		Target     string `json:"target"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	if req.PathPrefix == "" || req.Target == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "pathPrefix and target required"})
		return
	}
	rule := Rule{
		ID:         uuid.New().String(),
		PathPrefix: req.PathPrefix,
		Target:     req.Target,
	}
	h.manager.AddRule(rule)
	c.JSON(http.StatusCreated, rule)
}

func (h *APIHandler) DeleteRule(c *gin.Context) {
	id := c.Param("id")
	if h.manager.RemoveRule(id) {
		c.JSON(http.StatusOK, gin.H{"success": true})
	} else {
		c.JSON(http.StatusNotFound, gin.H{"error": "rule not found"})
	}
}
