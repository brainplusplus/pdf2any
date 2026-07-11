#!/usr/bin/env node
/**
 * Node.js wrapper example for pdf2any.
 *
 * Uses child_process.execFile to invoke the pdf2any binary.
 *
 * Platform resolution:
 *   process.platform → 'darwin' | 'linux' | 'win32'
 *   process.arch     → 'x64' | 'arm64'
 *   Map: darwin→macos, linux→linux, win32→windows; x64→amd64
 */

const { execFile } = require('child_process');
const path = require('path');

/**
 * Resolve the pdf2any binary path for the current platform.
 * In production, you would ship platform-specific binaries and
 * select the correct one based on process.platform + process.arch.
 */
function getBinaryPath() {
  const platform = process.platform;  // 'darwin' | 'linux' | 'win32'
  const arch = process.arch;          // 'x64' | 'arm64'

  const osMap = { darwin: 'macos', linux: 'linux', win32: 'windows' };
  const archMap = { x64: 'amd64', arm64: 'arm64' };

  const osName = osMap[platform] || platform;
  const archName = archMap[arch] || arch;
  const ext = platform === 'win32' ? '.exe' : '';

  const binaryName = `pdf2any-${osName}-${archName}${ext}`;
  return path.join(__dirname, 'bin', binaryName);
}

/**
 * Convert a PDF file to the specified format.
 *
 * @param {string} inputPath - Path to the input PDF.
 * @param {string} format - Output format (markdown, html, prosemirror, etc.).
 * @param {string} outputPath - Path for the output file.
 * @returns {Promise<{stdout: string, stderr: string}>}
 */
function convertPdf(inputPath, format, outputPath) {
  return new Promise((resolve, reject) => {
    const binaryPath = getBinaryPath();

    execFile(
      binaryPath,
      [inputPath, '-t', format, '-o', outputPath],
      { maxBuffer: 10 * 1024 * 1024 },  // 10MB buffer
      (err, stdout, stderr) => {
        if (err) {
          // err.code contains the exit code
          const error = new Error(`pdf2any exited with code ${err.code}: ${stderr}`);
          error.exitCode = err.code;
          error.stderr = stderr;
          error.stdout = stdout;
          reject(error);
        } else {
          resolve({ stdout, stderr });
        }
      }
    );
  });
}

// Example usage
async function main() {
  try {
    const result = await convertPdf('input.pdf', 'markdown', 'out.md');
    console.log('Conversion successful!');
    console.log('stdout:', result.stdout);
  } catch (err) {
    console.error(`Conversion failed (exit ${err.exitCode}):`, err.message);
    process.exit(err.exitCode || 1);
  }
}

// Export for use as a module
module.exports = { convertPdf, getBinaryPath };

// Run if called directly
if (require.main === module) {
  main();
}
