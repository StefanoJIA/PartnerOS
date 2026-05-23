/**
 * D3: Build PyInstaller sidecar and copy to src-tauri/binaries with Rust target triple suffix
 * (required by Tauri externalBin).
 *
 * Uses a fresh --distpath/--workpath each run so a locked `dist/intellioffice-backend.exe`
 * (e.g. still running) does not break the build.
 */
import { execSync } from 'node:child_process'
import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..', '..')
const backendDir = path.join(repoRoot, 'backend')
const outDir = path.join(repoRoot, 'frontend', 'src-tauri', 'binaries')

function main() {
  const triple = execSync('rustc --print host-tuple', { encoding: 'utf8' }).trim()
  if (!triple) {
    console.error('rustc --print host-tuple failed (install Rust)')
    process.exit(1)
  }
  const ext = process.platform === 'win32' ? '.exe' : ''
  const destName = `intellioffice-backend-${triple}${ext}`

  mkdirSync(outDir, { recursive: true })

  const stamp = Date.now()
  const sideDist = path.join(backendDir, `dist-sidecar-${stamp}`)
  const sideWork = path.join(backendDir, `build-sidecar-${stamp}`)

  const q = (p) => `"${path.normalize(p)}"`
  execSync(
    `pyinstaller intellioffice-backend.spec --noconfirm --distpath ${q(sideDist)} --workpath ${q(sideWork)}`,
    {
      cwd: backendDir,
      stdio: 'inherit',
      shell: true,
    },
  )

  const built = path.join(sideDist, `intellioffice-backend${ext}`)
  if (!existsSync(built)) {
    console.error('PyInstaller output missing:', built)
    process.exit(1)
  }

  const dest = path.join(outDir, destName)
  copyFileSync(built, dest)
  console.log('Prepared Tauri sidecar:', dest)
}

main()
