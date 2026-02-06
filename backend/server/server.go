package server

import (
	"encoding/json"
	"fmt"
	"image"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/gorilla/websocket"

	"github.com/xxnuo/localctrl/auth"
	"github.com/xxnuo/localctrl/capture"
	"github.com/xxnuo/localctrl/chat"
	"github.com/xxnuo/localctrl/clipboard"
	"github.com/xxnuo/localctrl/config"
	"github.com/xxnuo/localctrl/filemanager"
	"github.com/xxnuo/localctrl/input"
	"github.com/xxnuo/localctrl/proxy"
	"github.com/xxnuo/localctrl/sysinfo"
	"github.com/xxnuo/localctrl/terminal"
	"github.com/xxnuo/localctrl/ws"
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  1024 * 64,
	WriteBufferSize: 1024 * 64,
}

type Server struct {
	cfg         *config.Config
	router      *gin.Engine
	authHandler *auth.Handler
	authStore   *auth.Store
	hub         *ws.Hub
	capturer    *capture.Capturer
	jpegEncoder *capture.JPEGEncoder
	clipMgr     *clipboard.Manager
	termMgr     *terminal.Manager
	fileMgr     *filemanager.Handler
	proxyMgr    *proxy.Manager
	proxyAPI    *proxy.APIHandler
	chatMgr     *chat.Manager

	streaming   bool
	streamMu    sync.Mutex
	fps         int
	hwEncoder   string
	hwAvailable bool
}

func New(cfg *config.Config) (*Server, error) {
	gin.SetMode(gin.ReleaseMode)

	dbPath := config.ConfigDir() + "/localctrl.db"
	store, err := auth.NewStore(dbPath)
	if err != nil {
		return nil, fmt.Errorf("auth store: %w", err)
	}

	if err := store.EnsureDefaultUser(cfg.DefaultUser.Username, cfg.DefaultUser.Password); err != nil {
		return nil, fmt.Errorf("ensure default user: %w", err)
	}

	hwEncoder, hwAvailable := capture.DetectHardwareEncoder()
	if hwAvailable {
		log.Printf("Hardware encoder detected: %s", hwEncoder)
	} else {
		log.Println("No hardware encoder, using JPEG software encoding")
	}

	s := &Server{
		cfg:         cfg,
		authHandler: auth.NewHandler(store, cfg.JWTSecret, cfg.Password),
		authStore:   store,
		capturer:    capture.NewCapturer(),
		jpegEncoder: capture.NewJPEGEncoder(60),
		termMgr:     terminal.NewManager(),
		fileMgr:     filemanager.NewHandler(),
		proxyMgr:    proxy.NewManager(),
		fps:         20,
		hwEncoder:   hwEncoder,
		hwAvailable: hwAvailable,
	}

	s.proxyAPI = proxy.NewAPIHandler(s.proxyMgr)

	s.chatMgr = chat.NewManager(func(msg chat.Message) {
		data, _ := json.Marshal(ws.ChatMessageMsg{
			Type:      ws.MsgChatMessage,
			ID:        msg.ID,
			Sender:    msg.Sender,
			Text:      msg.Text,
			Timestamp: msg.Timestamp,
		})
		s.hub.Broadcast(data)
	})

	s.hub = ws.NewHub(s.handleWSMessage)

	s.clipMgr = clipboard.NewManager(func(text string) {
		data, _ := json.Marshal(ws.ClipboardSyncMsg{
			Type: ws.MsgClipboardSync,
			Text: text,
		})
		s.hub.Broadcast(data)
	})

	s.setupRouter()
	return s, nil
}

func (s *Server) setupRouter() {
	r := gin.New()
	r.Use(gin.Recovery())

	r.POST("/api/auth/login", s.authHandler.Login)
	r.POST("/api/auth/register", s.authHandler.Register)

	api := r.Group("/api")
	api.Use(s.jwtMiddleware())
	{
		api.GET("/sysinfo", s.handleSysInfo)
		api.GET("/files", s.fileMgr.List)
		api.POST("/files/mkdir", s.fileMgr.Mkdir)
		api.POST("/files/delete", s.fileMgr.Delete)
		api.POST("/files/rename", s.fileMgr.Rename)
		api.POST("/files/move", s.fileMgr.Move)
		api.POST("/files/upload", s.fileMgr.Upload)
		api.GET("/files/download", s.fileMgr.Download)
		api.GET("/proxy/rules", s.proxyAPI.GetRules)
		api.POST("/proxy/rules", s.proxyAPI.AddRule)
		api.DELETE("/proxy/rules/:id", s.proxyAPI.DeleteRule)
	}

	r.GET("/ws/screen", s.handleScreenWS)
	r.GET("/ws/terminal/:id", s.handleTerminalWS)
	r.GET("/ws/chat", s.handleChatWS)

	r.Any("/proxy/*path", gin.WrapH(s.proxyMgr))

	r.NoRoute(s.serveStaticFiles())

	s.router = r
}

func (s *Server) jwtMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenStr := c.GetHeader("Authorization")
		if tokenStr == "" {
			tokenStr = c.Query("token")
		}
		tokenStr = strings.TrimPrefix(tokenStr, "Bearer ")

		if tokenStr == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "no token"})
			return
		}

		claims, err := auth.ValidateToken(s.cfg.JWTSecret, tokenStr)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			return
		}

		c.Set("username", claims.Username)
		c.Next()
	}
}

func (s *Server) handleSysInfo(c *gin.Context) {
	info, err := sysinfo.Collect()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, info)
}

func (s *Server) handleScreenWS(c *gin.Context) {
	tokenStr := c.Query("token")
	claims, err := auth.ValidateToken(s.cfg.JWTSecret, tokenStr)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		return
	}

	client := ws.NewClient(uuid.New().String(), claims.Username, conn, s.hub)
	s.hub.Register(client)

	s.sendScreenInfo(client)
	s.sendMonitorList(client)
	s.startStreamingIfNeeded()

	go client.WritePump()
	go client.ReadPump()
}

func (s *Server) handleTerminalWS(c *gin.Context) {
	tokenStr := c.Query("token")
	_, err := auth.ValidateToken(s.cfg.JWTSecret, tokenStr)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	termID := c.Param("id")
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		return
	}
	defer conn.Close()

	sess, err := s.termMgr.Create(termID)
	if err != nil {
		conn.WriteMessage(websocket.TextMessage, []byte("Failed to create terminal: "+err.Error()))
		return
	}
	defer s.termMgr.Close(termID)

	done := make(chan struct{})

	go func() {
		defer close(done)
		buf := make([]byte, 4096)
		for {
			n, err := sess.Read(buf)
			if err != nil {
				return
			}
			if err := conn.WriteMessage(websocket.BinaryMessage, buf[:n]); err != nil {
				return
			}
		}
	}()

	go func() {
		for {
			msgType, data, err := conn.ReadMessage()
			if err != nil {
				return
			}
			if msgType == websocket.TextMessage {
				var msg struct {
					Type string `json:"type"`
					Rows uint16 `json:"rows"`
					Cols uint16 `json:"cols"`
				}
				if json.Unmarshal(data, &msg) == nil && msg.Type == "resize" {
					sess.Resize(msg.Rows, msg.Cols)
					continue
				}
			}
			sess.Write(data)
		}
	}()

	<-done
}

func (s *Server) handleChatWS(c *gin.Context) {
	tokenStr := c.Query("token")
	claims, err := auth.ValidateToken(s.cfg.JWTSecret, tokenStr)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		return
	}
	defer conn.Close()

	history := s.chatMgr.History()
	for _, msg := range history {
		data, _ := json.Marshal(ws.ChatMessageMsg{
			Type:      ws.MsgChatMessage,
			ID:        msg.ID,
			Sender:    msg.Sender,
			Text:      msg.Text,
			Timestamp: msg.Timestamp,
		})
		conn.WriteMessage(websocket.TextMessage, data)
	}

	for {
		_, data, err := conn.ReadMessage()
		if err != nil {
			return
		}
		var msg struct {
			Text string `json:"text"`
		}
		if json.Unmarshal(data, &msg) == nil && msg.Text != "" {
			s.chatMgr.Add(claims.Username, msg.Text)
		}
	}
}

func (s *Server) handleWSMessage(client *ws.Client, msgType int, data []byte) {
	if msgType == websocket.TextMessage {
		var base ws.BaseMessage
		if err := json.Unmarshal(data, &base); err != nil {
			return
		}
		switch base.Type {
		case ws.MsgPing:
			var ping ws.PingMsg
			json.Unmarshal(data, &ping)
			pong := ws.PongMsg{Type: ws.MsgPong, Timestamp: ping.Timestamp}
			resp, _ := json.Marshal(pong)
			s.hub.SendToClient(client.ID, resp)

		case ws.MsgMouseEvent:
			if !s.hub.IsController(client.ID) {
				return
			}
			var msg ws.MouseEventMsg
			json.Unmarshal(data, &msg)
			s.handleMouseEvent(msg)

		case ws.MsgKeyboardEvent:
			if !s.hub.IsController(client.ID) {
				return
			}
			var msg ws.KeyboardEventMsg
			json.Unmarshal(data, &msg)
			s.handleKeyboardEvent(msg)

		case ws.MsgSpecialKey:
			if !s.hub.IsController(client.ID) {
				return
			}
			var msg ws.SpecialKeyMsg
			json.Unmarshal(data, &msg)
			input.HandleSpecialKey(msg.Key)

		case ws.MsgMonitorSwitch:
			var msg ws.MonitorSwitchMsg
			json.Unmarshal(data, &msg)
			s.capturer.SetMonitor(msg.Index)
			s.sendScreenInfo(client)

		case ws.MsgConfigUpdate:
			var msg ws.ConfigUpdateMsg
			json.Unmarshal(data, &msg)
			if msg.FPS != nil && *msg.FPS >= 5 && *msg.FPS <= 30 {
				s.streamMu.Lock()
				s.fps = *msg.FPS
				s.streamMu.Unlock()
			}
			if msg.Quality != nil {
				s.jpegEncoder.SetQuality(*msg.Quality)
			}

		case ws.MsgControlRequest:
			s.hub.RequestControl(client.ID)

		case ws.MsgClipboardSync:
			var msg ws.ClipboardSyncMsg
			json.Unmarshal(data, &msg)
			s.clipMgr.SetText(msg.Text)
		}
	}
}

func (s *Server) handleMouseEvent(msg ws.MouseEventMsg) {
	bounds := s.capturer.Bounds()
	x := int(msg.X * float64(bounds.Dx()))
	y := int(msg.Y * float64(bounds.Dy()))
	x += bounds.Min.X
	y += bounds.Min.Y

	switch msg.Action {
	case "move":
		input.MoveMouse(x, y)
	case "down":
		input.MoveMouse(x, y)
		input.MouseDown(msg.Button)
	case "up":
		input.MoveMouse(x, y)
		input.MouseUp(msg.Button)
	case "scroll":
		input.MouseScroll(int(msg.ScrollX), int(msg.ScrollY))
	}
}

func (s *Server) handleKeyboardEvent(msg ws.KeyboardEventMsg) {
	key := input.MapKey(msg.Key)
	switch msg.Action {
	case "down":
		input.KeyDown(key)
	case "up":
		input.KeyUp(key)
	}
}

func (s *Server) sendScreenInfo(client *ws.Client) {
	bounds := s.capturer.Bounds()
	encoding := "jpeg"
	if s.hwAvailable {
		encoding = "h264"
	}
	msg := ws.ScreenInfoMsg{
		Type:         ws.MsgScreenInfo,
		Width:        bounds.Dx(),
		Height:       bounds.Dy(),
		MonitorIndex: s.capturer.MonitorIndex(),
		Encoding:     encoding,
	}
	data, _ := json.Marshal(msg)
	s.hub.SendToClient(client.ID, data)
}

func (s *Server) sendMonitorList(client *ws.Client) {
	monitors := capture.ListMonitors()
	wsMonitors := make([]ws.MonitorInfo, len(monitors))
	for i, m := range monitors {
		wsMonitors[i] = ws.MonitorInfo{
			Index:   m.Index,
			Name:    m.Name,
			Width:   m.Width,
			Height:  m.Height,
			Primary: m.Primary,
		}
	}
	msg := ws.MonitorListMsg{
		Type:     ws.MsgMonitorList,
		Monitors: wsMonitors,
	}
	data, _ := json.Marshal(msg)
	s.hub.SendToClient(client.ID, data)
}

func (s *Server) startStreamingIfNeeded() {
	s.streamMu.Lock()
	defer s.streamMu.Unlock()
	if s.streaming {
		return
	}
	s.streaming = true
	go s.streamLoop()
}

func (s *Server) streamLoop() {
	var lastImg *image.RGBA
	_ = lastImg

	for {
		if s.hub.ClientCount() == 0 {
			s.streamMu.Lock()
			s.streaming = false
			s.streamMu.Unlock()
			return
		}

		s.streamMu.Lock()
		fps := s.fps
		s.streamMu.Unlock()

		img, err := s.capturer.Capture()
		if err != nil {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		data, err := s.jpegEncoder.Encode(img)
		if err != nil {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		s.hub.Broadcast(data)
		lastImg = img

		time.Sleep(time.Second / time.Duration(fps))
	}
}

func (s *Server) serveStaticFiles() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "LocalCtrl API server running", "version": "1.0.0"})
	}
}

func (s *Server) SetStaticHandler(h gin.HandlerFunc) {
	s.router.NoRoute(h)
}

func (s *Server) Run() error {
	go s.hub.Run()
	s.clipMgr.StartWatching()
	defer s.clipMgr.Stop()
	defer s.termMgr.CloseAll()

	addr := fmt.Sprintf(":%d", s.cfg.Port)

	certPath, keyPath, err := EnsureTLSCert(
		config.ConfigDir(),
		s.cfg.TLS.Cert,
		s.cfg.TLS.Key,
	)
	if err != nil {
		return fmt.Errorf("TLS cert: %w", err)
	}

	log.Printf("LocalCtrl server starting on https://0.0.0.0%s", addr)
	return s.router.RunTLS(addr, certPath, keyPath)
}

func (s *Server) Close() {
	s.authStore.Close()
}

func (s *Server) SetStaticHandler(h gin.HandlerFunc) {
	s.router.NoRoute(h)
}
