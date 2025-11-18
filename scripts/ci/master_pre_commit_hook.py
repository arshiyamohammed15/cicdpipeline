#!/usr/bin/env python3
"""
Master Pre-Commit Hook - Complete replacement for pre-commit framework
This hook implements the desired behavior:
1. Auto-fixes violations when possible
2. Asks for confirmation before proceeding with commit
3. Never blocks commits - always allows them to proceed

This completely bypasses pre-commit framework stashing issues.
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Get project root
project_root = Path(__file__).parent.parent.parent

class MasterPreCommitHook:
    def __init__(self):
        self.project_root = project_root
        self.fixed_files = []
        self.violations_found = False

    def run_command(self, cmd: List[str], cwd: Path = None, capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def get_modified_files(self) -> List[str]:
        """Get all modified files (staged + unstaged)"""
        returncode, stdout, stderr = self.run_command(["git", "status", "--porcelain"])
        if returncode != 0:
            return []

        files = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                # Extract filename (handle renames)
                filename = line[3:].split(' -> ')[-1].strip()
                if filename:
                    files.append(filename)
        return files

    def stage_all_modified_files(self) -> int:
        """Stage all modified files. Returns count staged."""
        before_files = set()
        returncode, stdout, stderr = self.run_command(["git", "diff", "--cached", "--name-only"])
        if returncode == 0:
            before_files = set(f.strip() for f in stdout.split('\n') if f.strip())

        # Stage all modified files
        self.run_command(["git", "add", "-u"])

        after_files = set()
        returncode, stdout, stderr = self.run_command(["git", "diff", "--cached", "--name-only"])
        if returncode == 0:
            after_files = set(f.strip() for f in stdout.split('\n') if f.strip())

        return len(after_files - before_files)

    def run_eol_validator(self) -> Tuple[bool, str]:
        """Run EOL validator and return (success, message)"""
        print("Running EOL validation...")
        returncode, stdout, stderr = self.run_command([
            sys.executable, str(self.project_root / "scripts" / "ci" / "validate_eol.py"), "--fix"
        ])

        if "Fixed EOL issues:" in stdout:
            # Parse fixed files
            lines = stdout.split('\n')
            in_fixed_section = False
            for line in lines:
                if 'Fixed EOL issues:' in line:
                    in_fixed_section = True
                    continue
                if in_fixed_section:
                    if 'Fixed EOL' in line and ':' in line:
                        file_path = line.strip().split(':', 1)[0].strip()
                        if file_path and Path(self.project_root / file_path).exists():
                            self.fixed_files.append(file_path)
                    elif line.strip() == '':
                        break

            if self.fixed_files:
                return True, f"[OK] Fixed EOL issues in {len(self.fixed_files)} file(s)"
            else:
                return True, "[OK] EOL validation passed"
        elif returncode == 0:
            return True, "[OK] EOL validation passed"
        else:
            return False, f"[WARN] EOL validation: {stderr or stdout}"

    def run_formation_hooks(self) -> Tuple[bool, List[str]]:
        """Run standard formatting hooks and return (success, fixed_files)"""
        print("Running code formatting...")
        fixed_files = []

        # Run trailing whitespace fixer
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "pre_commit_hooks.trailing_whitespace_fixer"
        ], cwd=self.project_root)

        if returncode != 0 and stdout.strip():
            # Parse which files were fixed
            for line in stdout.split('\n'):
                if line.strip() and not line.startswith('Fixing'):
                    continue
                if 'Fixing' in line:
                    file_path = line.replace('Fixing', '').strip()
                    if file_path and Path(self.project_root / file_path).exists():
                        fixed_files.append(file_path)

        # Run end-of-file fixer
        returncode2, stdout2, stderr2 = self.run_command([
            "python", "-m", "pre_commit_hooks.end_of_file_fixer"
        ], cwd=self.project_root)

        if returncode2 != 0 and stdout2.strip():
            for line in stdout2.split('\n'):
                if 'Fixing' in line:
                    file_path = line.replace('Fixing', '').strip()
                    if file_path and Path(self.project_root / file_path).exists():
                        fixed_files.append(file_path)

        # Run mixed line ending fixer
        returncode3, stdout3, stderr3 = self.run_command([
            "python", "-m", "pre_commit_hooks.mixed_line_ending",
            "--fix=lf"
        ], cwd=self.project_root)

        if fixed_files:
            return True, fixed_files
        return True, []  # These hooks don't block

    def run_constitution_validator(self) -> Tuple[bool, str]:
        """Run constitution validator and return (success, message)"""
        print("Running constitution validation...")
        returncode, stdout, stderr = self.run_command([
            sys.executable, str(self.project_root / "tools" / "enhanced_cli.py"), "--directory", "."
        ])

        if returncode == 0:
            return True, "[OK] Constitution validation passed"
        else:
            self.violations_found = True
            return False, f"[WARN] Constitution violations found:\n{stdout}\n{stderr}"

    def stage_fixed_files(self, files_to_stage: List[str]) -> int:
        """Stage specific files. Returns count staged."""
        staged_count = 0
        for file_path in files_to_stage:
            returncode, stdout, stderr = self.run_command(["git", "add", str(file_path)])
            if returncode == 0:
                staged_count += 1
        return staged_count

    def ask_confirmation(self) -> bool:
        """Ask user for confirmation to proceed with commit"""
        if not self.fixed_files and not self.violations_found:
            return True  # No fixes needed, auto-proceed

        print("\n" + "="*60)
        print("PRE-COMMIT HOOK SUMMARY")
        print("="*60)

        if self.fixed_files:
            print(f"[OK] Auto-fixed {len(self.fixed_files)} file(s):")
            for file in self.fixed_files[:10]:  # Show first 10
                print(f"  - {file}")
            if len(self.fixed_files) > 10:
                print(f"  ... and {len(self.fixed_files) - 10} more")
            print()

        if self.violations_found:
            print("[WARN] Some issues could not be auto-fixed.")
            print("  These will be reported but won't block the commit.")
            print()

        # Ask for confirmation
        try:
            response = input("Proceed with commit? (Y/n): ").strip().lower()
            return response in ['', 'y', 'yes']
        except (EOFError, KeyboardInterrupt):
            # If input fails (e.g., in IDE), auto-proceed
            print("[OK] Auto-proceeding with commit (IDE mode)")
            return True

    def run(self) -> int:
        """Main hook execution"""
        print("Starting ZeroUI Pre-Commit Hook")
        print("  (Auto-fixes violations and never blocks commits)")
        print()

        try:
            # Step 1: Stage all modified files upfront
            staged_count = self.stage_all_modified_files()
            if staged_count > 0:
                print(f"[OK] Staged {staged_count} modified file(s)")
            print()

            # Step 2: Run EOL validator
            success, message = self.run_eol_validator()
            print(message)
            if not success:
                print("  (Non-blocking - continuing)")
            print()

            # Step 3: Run formatting hooks
            success, fixed_files = self.run_formation_hooks()
            if fixed_files:
                self.fixed_files.extend(fixed_files)
                staged = self.stage_fixed_files(fixed_files)
                print(f"[OK] Fixed formatting in {len(fixed_files)} file(s)")
                if staged > 0:
                    print(f"[OK] Staged {staged} fixed file(s)")
            else:
                print("[OK] Code formatting passed")
            print()

            # Step 4: Run constitution validator
            success, message = self.run_constitution_validator()
            print(message)
            if not success:
                print("  (Non-blocking - continuing)")
            print()

            # Step 5: Ask for confirmation
            if self.ask_confirmation():
                print("\n[SUCCESS] Proceeding with commit...")
                return 0  # Success - allow commit
            else:
                print("\n[CANCELLED] Commit cancelled by user")
                return 1  # Fail - block commit

        except Exception as e:
            print(f"[ERROR] Pre-commit hook error: {e}")
            print("  (Non-blocking - proceeding with commit)")
            print()
            return 0  # Never block on errors

def main():
    hook = MasterPreCommitHook()
    return hook.run()

if __name__ == "__main__":
    sys.exit(main())
