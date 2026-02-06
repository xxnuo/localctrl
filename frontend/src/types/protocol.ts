export interface MouseEvent {
  type: 'mouse_event'
  x: number
  y: number
  button: 'left' | 'right' | 'middle' | 'none'
  action: 'move' | 'down' | 'up' | 'scroll'
  scrollX?: number
  scrollY?: number
}

export interface KeyboardEvent {
  type: 'keyboard_event'
  key: string
  code: string
  action: 'down' | 'up'
  modifiers: {
    ctrl: boolean
    alt: boolean
    shift: boolean
    meta: boolean
  }
}

export interface ScreenInfo {
  type: 'screen_info'
  width: number
  height: number
  monitorIndex: number
  encoding: 'jpeg' | 'h264'
}

export interface MonitorList {
  type: 'monitor_list'
  monitors: { index: number; name: string; width: number; height: number; primary: boolean }[]
}

export interface MonitorSwitch {
  type: 'monitor_switch'
  index: number
}

export interface ConfigUpdate {
  type: 'config_update'
  fps?: number
  quality?: number
}

export interface ControlRequest {
  type: 'control_request'
}

export interface ControlGrant {
  type: 'control_grant'
  granted: boolean
  controller?: string
}

export interface ClipboardSync {
  type: 'clipboard_sync'
  text: string
}

export interface Stats {
  type: 'stats'
  bandwidth: number
  fps: number
  encoding: string
}

export interface SpecialKey {
  type: 'special_key'
  key: 'ctrl_alt_del' | 'win' | 'print_screen'
}

export interface ChatMessage {
  type: 'chat_message'
  id: string
  sender: string
  text: string
  timestamp: number
}

export interface Ping {
  type: 'ping'
  timestamp: number
}

export interface Pong {
  type: 'pong'
  timestamp: number
}

export type WSMessage =
  | MouseEvent
  | KeyboardEvent
  | ScreenInfo
  | MonitorList
  | MonitorSwitch
  | ConfigUpdate
  | ControlRequest
  | ControlGrant
  | ClipboardSync
  | Stats
  | SpecialKey
  | ChatMessage
  | Ping
  | Pong

export interface FileEntry {
  name: string
  path: string
  isDir: boolean
  size: number
  modTime: string
  mode: string
}

export interface SysInfo {
  hostname: string
  os: string
  arch: string
  cpuModel: string
  cpuCores: number
  cpuUsage: number
  memTotal: number
  memUsed: number
  gpu: string
  network: { name: string; ip: string }[]
}

export interface ProxyRule {
  id: string
  pathPrefix: string
  target: string
}

export interface AuthResponse {
  token: string
  username: string
}
