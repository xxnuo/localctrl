package capture

import (
	"fmt"
	"image"
	"io"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"sync"
)

type H264Encoder struct {
	mu      sync.Mutex
	cmd     *exec.Cmd
	stdin   io.WriteCloser
	stdout  io.ReadCloser
	width   int
	height  int
	fps     int
	running bool
}

func DetectHardwareEncoder() (encoder string, available bool) {
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		return "", false
	}

	if runtime.GOOS == "linux" {
		if _, err := os.Stat("/dev/dri/renderD128"); err == nil {
			out, err := exec.Command("ffmpeg", "-hide_banner", "-encoders").Output()
			if err == nil && strings.Contains(string(out), "h264_vaapi") {
				return "h264_vaapi", true
			}
		}

		out, err := exec.Command("ffmpeg", "-hide_banner", "-encoders").Output()
		if err == nil && strings.Contains(string(out), "h264_qsv") {
			return "h264_qsv", true
		}
	}

	return "", false
}

func NewH264Encoder(width, height, fps int, hwEncoder string) (*H264Encoder, error) {
	args := buildFFmpegArgs(width, height, fps, hwEncoder)

	cmd := exec.Command("ffmpeg", args...)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("stdin pipe: %w", err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("stdout pipe: %w", err)
	}
	cmd.Stderr = nil

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("start ffmpeg: %w", err)
	}

	return &H264Encoder{
		cmd:     cmd,
		stdin:   stdin,
		stdout:  stdout,
		width:   width,
		height:  height,
		fps:     fps,
		running: true,
	}, nil
}

func buildFFmpegArgs(width, height, fps int, hwEncoder string) []string {
	args := []string{
		"-hide_banner",
		"-f", "rawvideo",
		"-pix_fmt", "rgba",
		"-s", fmt.Sprintf("%dx%d", width, height),
		"-r", fmt.Sprintf("%d", fps),
		"-i", "pipe:0",
	}

	if hwEncoder == "h264_vaapi" {
		args = append(args,
			"-vaapi_device", "/dev/dri/renderD128",
			"-vf", "format=nv12,hwupload",
			"-c:v", "h264_vaapi",
		)
	} else if hwEncoder == "h264_qsv" {
		args = append(args, "-c:v", "h264_qsv")
	} else {
		args = append(args,
			"-c:v", "libx264",
			"-preset", "ultrafast",
			"-tune", "zerolatency",
		)
	}

	args = append(args,
		"-f", "h264",
		"-g", fmt.Sprintf("%d", fps),
		"pipe:1",
	)
	return args
}

func (e *H264Encoder) WriteFrame(img *image.RGBA) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	if !e.running {
		return fmt.Errorf("encoder not running")
	}
	_, err := e.stdin.Write(img.Pix)
	return err
}

func (e *H264Encoder) Read(buf []byte) (int, error) {
	return e.stdout.Read(buf)
}

func (e *H264Encoder) Close() error {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.running = false
	e.stdin.Close()
	return e.cmd.Wait()
}

func (e *H264Encoder) EncodingType() string {
	return "h264"
}
