package capture

import (
	"bytes"
	"image"
	"image/jpeg"
	"sync"
)

type JPEGEncoder struct {
	mu      sync.Mutex
	quality int
	buf     bytes.Buffer
}

func NewJPEGEncoder(quality int) *JPEGEncoder {
	if quality < 1 {
		quality = 60
	}
	return &JPEGEncoder{quality: quality}
}

func (e *JPEGEncoder) SetQuality(q int) {
	e.mu.Lock()
	defer e.mu.Unlock()
	if q >= 1 && q <= 100 {
		e.quality = q
	}
}

func (e *JPEGEncoder) Quality() int {
	e.mu.Lock()
	defer e.mu.Unlock()
	return e.quality
}

func (e *JPEGEncoder) Encode(img image.Image) ([]byte, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	e.buf.Reset()
	err := jpeg.Encode(&e.buf, img, &jpeg.Options{Quality: e.quality})
	if err != nil {
		return nil, err
	}
	result := make([]byte, e.buf.Len())
	copy(result, e.buf.Bytes())
	return result, nil
}

func (e *JPEGEncoder) EncodingType() string {
	return "jpeg"
}
