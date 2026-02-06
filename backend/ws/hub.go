package ws

import (
	"encoding/json"
	"log"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type Client struct {
	ID       string
	Username string
	Conn     *websocket.Conn
	send     chan []byte
	hub      *Hub
	mu       sync.Mutex
}

type Hub struct {
	mu         sync.RWMutex
	clients    map[string]*Client
	controller *Client
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client

	onMessage func(client *Client, msgType int, data []byte)
}

func NewHub(onMessage func(client *Client, msgType int, data []byte)) *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		broadcast:  make(chan []byte, 256),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		onMessage:  onMessage,
	}
}

func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			if h.controller == nil {
				h.controller = client
				h.notifyControlGrant(client, true)
			}
			h.mu.Unlock()
			log.Printf("Client connected: %s (%s)", client.ID, client.Username)

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.send)
				if h.controller == client {
					h.controller = nil
					for _, c := range h.clients {
						h.controller = c
						h.notifyControlGrant(c, true)
						break
					}
				}
			}
			h.mu.Unlock()
			log.Printf("Client disconnected: %s", client.ID)

		case msg := <-h.broadcast:
			h.mu.RLock()
			for _, client := range h.clients {
				select {
				case client.send <- msg:
				default:
					go func(c *Client) {
						h.unregister <- c
					}(client)
				}
			}
			h.mu.RUnlock()
		}
	}
}

func (h *Hub) Broadcast(data []byte) {
	h.broadcast <- data
}

func (h *Hub) BroadcastJSON(v interface{}) {
	data, err := json.Marshal(v)
	if err != nil {
		return
	}
	h.broadcast <- data
}

func (h *Hub) SendToClient(clientID string, data []byte) {
	h.mu.RLock()
	client, ok := h.clients[clientID]
	h.mu.RUnlock()
	if ok {
		select {
		case client.send <- data:
		default:
		}
	}
}

func (h *Hub) IsController(clientID string) bool {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.controller != nil && h.controller.ID == clientID
}

func (h *Hub) RequestControl(clientID string) bool {
	h.mu.Lock()
	defer h.mu.Unlock()
	client, ok := h.clients[clientID]
	if !ok {
		return false
	}
	if h.controller != nil && h.controller.ID != clientID {
		h.notifyControlGrant(h.controller, false)
	}
	h.controller = client
	h.notifyControlGrant(client, true)
	return true
}

func (h *Hub) ReleaseControl(clientID string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.controller != nil && h.controller.ID == clientID {
		h.notifyControlGrant(h.controller, false)
		h.controller = nil
	}
}

func (h *Hub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

func (h *Hub) notifyControlGrant(client *Client, granted bool) {
	msg := ControlGrantMsg{
		Type:       MsgControlGrant,
		Granted:    granted,
		Controller: client.Username,
	}
	data, _ := json.Marshal(msg)
	for _, c := range h.clients {
		select {
		case c.send <- data:
		default:
		}
	}
}

func (h *Hub) Register(client *Client) {
	h.register <- client
}

func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

func NewClient(id, username string, conn *websocket.Conn, hub *Hub) *Client {
	return &Client{
		ID:       id,
		Username: username,
		Conn:     conn,
		send:     make(chan []byte, 256),
		hub:      hub,
	}
}

func (c *Client) ReadPump() {
	defer func() {
		c.hub.Unregister(c)
		c.Conn.Close()
	}()
	c.Conn.SetReadLimit(64 * 1024)
	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})
	for {
		msgType, data, err := c.Conn.ReadMessage()
		if err != nil {
			break
		}
		if c.hub.onMessage != nil {
			c.hub.onMessage(c, msgType, data)
		}
	}
}

func (c *Client) WritePump() {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()
	for {
		select {
		case msg, ok := <-c.send:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			c.mu.Lock()
			if len(msg) > 0 && msg[0] == '{' {
				c.Conn.WriteMessage(websocket.TextMessage, msg)
			} else {
				c.Conn.WriteMessage(websocket.BinaryMessage, msg)
			}
			c.mu.Unlock()
		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}
