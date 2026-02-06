package ws

type MessageType string

const (
	MsgMouseEvent     MessageType = "mouse_event"
	MsgKeyboardEvent  MessageType = "keyboard_event"
	MsgScreenInfo     MessageType = "screen_info"
	MsgMonitorList    MessageType = "monitor_list"
	MsgMonitorSwitch  MessageType = "monitor_switch"
	MsgConfigUpdate   MessageType = "config_update"
	MsgControlRequest MessageType = "control_request"
	MsgControlGrant   MessageType = "control_grant"
	MsgClipboardSync  MessageType = "clipboard_sync"
	MsgStats          MessageType = "stats"
	MsgSpecialKey     MessageType = "special_key"
	MsgChatMessage    MessageType = "chat_message"
	MsgPing           MessageType = "ping"
	MsgPong           MessageType = "pong"
)

type BaseMessage struct {
	Type MessageType `json:"type"`
}

type MouseEventMsg struct {
	Type    MessageType `json:"type"`
	X       float64     `json:"x"`
	Y       float64     `json:"y"`
	Button  string      `json:"button"`
	Action  string      `json:"action"`
	ScrollX float64     `json:"scrollX,omitempty"`
	ScrollY float64     `json:"scrollY,omitempty"`
}

type KeyboardEventMsg struct {
	Type      MessageType       `json:"type"`
	Key       string            `json:"key"`
	Code      string            `json:"code"`
	Action    string            `json:"action"`
	Modifiers KeyboardModifiers `json:"modifiers"`
}

type KeyboardModifiers struct {
	Ctrl  bool `json:"ctrl"`
	Alt   bool `json:"alt"`
	Shift bool `json:"shift"`
	Meta  bool `json:"meta"`
}

type ScreenInfoMsg struct {
	Type         MessageType `json:"type"`
	Width        int         `json:"width"`
	Height       int         `json:"height"`
	MonitorIndex int         `json:"monitorIndex"`
	Encoding     string      `json:"encoding"`
}

type MonitorInfo struct {
	Index   int    `json:"index"`
	Name    string `json:"name"`
	Width   int    `json:"width"`
	Height  int    `json:"height"`
	Primary bool   `json:"primary"`
}

type MonitorListMsg struct {
	Type     MessageType   `json:"type"`
	Monitors []MonitorInfo `json:"monitors"`
}

type MonitorSwitchMsg struct {
	Type  MessageType `json:"type"`
	Index int         `json:"index"`
}

type ConfigUpdateMsg struct {
	Type    MessageType `json:"type"`
	FPS     *int        `json:"fps,omitempty"`
	Quality *int        `json:"quality,omitempty"`
}

type ControlRequestMsg struct {
	Type MessageType `json:"type"`
}

type ControlGrantMsg struct {
	Type       MessageType `json:"type"`
	Granted    bool        `json:"granted"`
	Controller string      `json:"controller,omitempty"`
}

type ClipboardSyncMsg struct {
	Type MessageType `json:"type"`
	Text string      `json:"text"`
}

type StatsMsg struct {
	Type      MessageType `json:"type"`
	Bandwidth float64     `json:"bandwidth"`
	FPS       float64     `json:"fps"`
	Encoding  string      `json:"encoding"`
}

type SpecialKeyMsg struct {
	Type MessageType `json:"type"`
	Key  string      `json:"key"`
}

type ChatMessageMsg struct {
	Type      MessageType `json:"type"`
	ID        string      `json:"id"`
	Sender    string      `json:"sender"`
	Text      string      `json:"text"`
	Timestamp int64       `json:"timestamp"`
}

type PingMsg struct {
	Type      MessageType `json:"type"`
	Timestamp int64       `json:"timestamp"`
}

type PongMsg struct {
	Type      MessageType `json:"type"`
	Timestamp int64       `json:"timestamp"`
}
