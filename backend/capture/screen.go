package capture

import (
	"image"
	"sync"

	"github.com/kbinani/screenshot"
)

type MonitorInfo struct {
	Index   int    `json:"index"`
	Name    string `json:"name"`
	Width   int    `json:"width"`
	Height  int    `json:"height"`
	Primary bool   `json:"primary"`
}

type Capturer struct {
	mu           sync.Mutex
	monitorIndex int
}

func NewCapturer() *Capturer {
	return &Capturer{monitorIndex: 0}
}

func (c *Capturer) SetMonitor(index int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	n := screenshot.NumActiveDisplays()
	if index >= 0 && index < n {
		c.monitorIndex = index
	}
}

func (c *Capturer) MonitorIndex() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.monitorIndex
}

func (c *Capturer) Capture() (*image.RGBA, error) {
	c.mu.Lock()
	idx := c.monitorIndex
	c.mu.Unlock()

	bounds := screenshot.GetDisplayBounds(idx)
	return screenshot.CaptureRect(bounds)
}

func (c *Capturer) Bounds() image.Rectangle {
	c.mu.Lock()
	idx := c.monitorIndex
	c.mu.Unlock()
	return screenshot.GetDisplayBounds(idx)
}

func ListMonitors() []MonitorInfo {
	n := screenshot.NumActiveDisplays()
	monitors := make([]MonitorInfo, n)
	for i := 0; i < n; i++ {
		b := screenshot.GetDisplayBounds(i)
		monitors[i] = MonitorInfo{
			Index:   i,
			Name:    "Display " + string(rune('1'+i)),
			Width:   b.Dx(),
			Height:  b.Dy(),
			Primary: i == 0,
		}
	}
	return monitors
}
