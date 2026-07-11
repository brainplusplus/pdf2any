package main

// Go wrapper example for pdf2any.
//
// Uses exec.Command to invoke the pdf2any binary.
//
// Platform resolution:
//
//	runtime.GOOS   → 'linux' | 'darwin' | 'windows'
//	runtime.GOARCH → 'amd64' | 'arm64'
//
// Map: darwin→macos, linux→linux, windows→windows

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
)

// getBinaryPath resolves the pdf2any binary path for the current platform.
// In production, you would ship platform-specific binaries and select
// the correct one based on runtime.GOOS + runtime.GOARCH.
func getBinaryPath() string {
	osName := runtime.GOOS
	archName := runtime.GOARCH

	// Map Go OS names to pdf2any artifact names
	osMap := map[string]string{
		"linux":   "linux",
		"darwin":  "macos",
		"windows": "windows",
	}

	mapped, ok := osMap[osName]
	if !ok {
		mapped = osName
	}

	binaryName := fmt.Sprintf("pdf2any-%s-%s", mapped, archName)
	if osName == "windows" {
		binaryName += ".exe"
	}
	return binaryName
}

// ConvertPDF converts a PDF file to the specified format.
//
// Returns stdout, stderr, and any error. If the process exited with a
// non-zero code, the error will be an *exec.ExitError with the exit code.
func ConvertPDF(inputPath, format, outputPath string) (string, string, error) {
	binaryPath := getBinaryPath()

	cmd := exec.Command(binaryPath, inputPath, "-t", format, "-o", outputPath)

	var stdout, stderr strings
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	return stdout, stderr, err
}

// WithJSONMode runs pdf2any with --json to get machine-readable metadata.
func ConvertPDFWithJSON(inputPath, format, outputPath string) (string, error) {
	binaryPath := getBinaryPath()

	cmd := exec.Command(binaryPath, inputPath, "-t", format, "-o", outputPath, "--json")

	var stdout, stderr strings
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return stdout, fmt.Errorf("pdf2any exited with code %d: %s",
				exitErr.ExitCode(), stderr.String())
		}
		return stdout, fmt.Errorf("failed to execute pdf2any: %w", err)
	}
	return stdout, nil
}

// strings is a simple string builder for capturing command output.
type strings struct {
	data []byte
}

func (s *strings) Write(p []byte) (int, error) {
	s.data = append(s.data, p...)
	return len(p), nil
}

func (s *strings) String() string {
	return string(s.data)
}

func main() {
	stdout, stderr, err := ConvertPDF("input.pdf", "markdown", "out.md")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Conversion failed: %v\n", err)
		fmt.Fprintf(os.Stderr, "stderr: %s\n", stderr)
		os.Exit(1)
	}
	fmt.Println("Conversion successful!")
	fmt.Println("stdout:", stdout)
}
