package sysinfo

import (
	"net"
	"os/exec"
	"runtime"
	"strings"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
)

type NetworkInterface struct {
	Name string `json:"name"`
	IP   string `json:"ip"`
}

type Info struct {
	Hostname string             `json:"hostname"`
	OS       string             `json:"os"`
	Arch     string             `json:"arch"`
	CPUModel string             `json:"cpuModel"`
	CPUCores int                `json:"cpuCores"`
	CPUUsage float64            `json:"cpuUsage"`
	MemTotal uint64             `json:"memTotal"`
	MemUsed  uint64             `json:"memUsed"`
	GPU      string             `json:"gpu"`
	Network  []NetworkInterface `json:"network"`
}

func Collect() (*Info, error) {
	hostInfo, _ := host.Info()
	cpuInfo, _ := cpu.Info()
	cpuPercent, _ := cpu.Percent(0, false)
	memInfo, _ := mem.VirtualMemory()

	info := &Info{
		Hostname: hostInfo.Hostname,
		OS:       hostInfo.Platform + " " + hostInfo.PlatformVersion,
		Arch:     runtime.GOARCH,
		MemTotal: memInfo.Total,
		MemUsed:  memInfo.Used,
	}

	if len(cpuInfo) > 0 {
		info.CPUModel = cpuInfo[0].ModelName
		info.CPUCores = int(cpuInfo[0].Cores)
	}
	if len(cpuPercent) > 0 {
		info.CPUUsage = cpuPercent[0]
	}

	info.GPU = detectGPU()
	info.Network = getNetworkInterfaces()

	return info, nil
}

func detectGPU() string {
	switch runtime.GOOS {
	case "linux":
		out, err := exec.Command("lspci").Output()
		if err != nil {
			return "N/A"
		}
		for _, line := range strings.Split(string(out), "\n") {
			lower := strings.ToLower(line)
			if strings.Contains(lower, "vga") || strings.Contains(lower, "3d") || strings.Contains(lower, "display") {
				parts := strings.SplitN(line, ": ", 2)
				if len(parts) == 2 {
					return strings.TrimSpace(parts[1])
				}
			}
		}
	case "darwin":
		out, _ := exec.Command("system_profiler", "SPDisplaysDataType").Output()
		for _, line := range strings.Split(string(out), "\n") {
			if strings.Contains(line, "Chipset Model") || strings.Contains(line, "Chip") {
				parts := strings.SplitN(line, ": ", 2)
				if len(parts) == 2 {
					return strings.TrimSpace(parts[1])
				}
			}
		}
	case "windows":
		out, _ := exec.Command("wmic", "path", "win32_videocontroller", "get", "name").Output()
		lines := strings.Split(string(out), "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" && line != "Name" {
				return line
			}
		}
	}
	return "N/A"
}

func getNetworkInterfaces() []NetworkInterface {
	var result []NetworkInterface
	ifaces, err := net.Interfaces()
	if err != nil {
		return result
	}
	for _, iface := range ifaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}
		addrs, _ := iface.Addrs()
		for _, addr := range addrs {
			if ipNet, ok := addr.(*net.IPNet); ok && ipNet.IP.To4() != nil {
				result = append(result, NetworkInterface{
					Name: iface.Name,
					IP:   ipNet.IP.String(),
				})
			}
		}
	}
	return result
}
