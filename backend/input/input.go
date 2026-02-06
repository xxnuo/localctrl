package input

import (
	"github.com/go-vgo/robotgo"
)

func MoveMouse(x, y int) {
	robotgo.Move(x, y)
}

func MouseClick(button string) {
	robotgo.Click(button, false)
}

func MouseDown(button string) {
	robotgo.Toggle(button, "down")
}

func MouseUp(button string) {
	robotgo.Toggle(button, "up")
}

func MouseScroll(dx, dy int) {
	robotgo.Scroll(dx, dy)
}

func KeyDown(key string) {
	robotgo.KeyDown(key)
}

func KeyUp(key string) {
	robotgo.KeyUp(key)
}

func KeyTap(key string, modifiers ...interface{}) {
	robotgo.KeyTap(key, modifiers...)
}

func SendCtrlAltDel() {
	robotgo.KeyTap("delete", "ctrl", "alt")
}

func SendWinKey() {
	robotgo.KeyTap("cmd")
}

func SendPrintScreen() {
	robotgo.KeyTap("printscreen")
}

func HandleSpecialKey(key string) {
	switch key {
	case "ctrl_alt_del":
		SendCtrlAltDel()
	case "win":
		SendWinKey()
	case "print_screen":
		SendPrintScreen()
	}
}

var keyMap = map[string]string{
	"Backspace":  "backspace",
	"Tab":        "tab",
	"Enter":      "enter",
	"Shift":      "shift",
	"Control":    "ctrl",
	"Alt":        "alt",
	"Escape":     "escape",
	"Space":      "space",
	"ArrowUp":    "up",
	"ArrowDown":  "down",
	"ArrowLeft":  "left",
	"ArrowRight": "right",
	"Delete":     "delete",
	"Home":       "home",
	"End":        "end",
	"PageUp":     "pageup",
	"PageDown":   "pagedown",
	"Insert":     "insert",
	"F1":         "f1",
	"F2":         "f2",
	"F3":         "f3",
	"F4":         "f4",
	"F5":         "f5",
	"F6":         "f6",
	"F7":         "f7",
	"F8":         "f8",
	"F9":         "f9",
	"F10":        "f10",
	"F11":        "f11",
	"F12":        "f12",
	"CapsLock":   "capslock",
	"NumLock":    "numlock",
	"ScrollLock": "scrolllock",
	"Meta":       "cmd",
}

func MapKey(jsKey string) string {
	if mapped, ok := keyMap[jsKey]; ok {
		return mapped
	}
	if len(jsKey) == 1 {
		return jsKey
	}
	return jsKey
}
