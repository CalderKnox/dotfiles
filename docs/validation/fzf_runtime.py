"""Actual fzf child-shell execution with a disposable controlling terminal."""
import errno
import os
import pty
import select
import shlex
import signal
import time
import unittest

from check import Fixture, ZSH, function_source


class FzfExecution(Fixture):
    def run_fzf(self, args, records="fixture:12:needle\n"):
        tool = self.require("fzf")
        data = self.cwd / "input"
        data.write_text(records)
        # pty.fork/login_tty gives the child a proper controlling terminal on macOS;
        # Popen preexec + TIOCSCTTY is not portable for repeated descriptor reuse.
        pid, master = pty.fork()
        if pid == 0:
            try:
                fd = os.open(data, os.O_RDONLY)
                os.dup2(fd, 0)
                os.close(fd)
                os.chdir(self.cwd)
                env = self.env | {"TERM": "xterm-256color"}
                os.execve(tool, [tool, "--no-height", "--sync", *args], env)
            finally:
                os._exit(127)
        output = bytearray()
        deadline = time.monotonic() + 10
        status = None
        tty_closed = False
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], max(0, deadline - time.monotonic()))
                if not ready:
                    break
                try:
                    chunk = os.read(master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        tty_closed = True
                        break
                    raise
                if not chunk:
                    tty_closed = True
                    break
                output.extend(chunk)
            if not tty_closed:
                os.kill(pid, signal.SIGKILL)
                _, status = os.waitpid(pid, 0)
                self.fail("fzf did not finish its bound action: " + output.decode(errors="replace")[-2000:])
            # EOF may precede the final process-exit bookkeeping. Reap normally;
            # a WNOHANG check here races a successfully aborting fzf process.
            _, status = os.waitpid(pid, 0)
            self.assertIn(os.waitstatus_to_exitcode(status), (0, 130), output.decode(errors="replace")[-2000:])
        finally:
            os.close(master)
            if status is None:
                try:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                except ProcessLookupError:
                    pass

    def test_tab_specific_shell_override_executes_zsh_preview_initialization(self):
        source = (ZSH / "fzf.zsh").read_text()
        self.assertIn("fzf-flags --with-shell='zsh -f -c'", source)
        output = self.cwd / "zsh-marker"
        action = "zmodload zsh/datetime; print -r -- zsh-preview > " + shlex.quote(str(output))
        self.run_fzf(["--with-shell=sh -c", "--with-shell=zsh -f -c",
                      f"--bind=start:execute-silent({action})+abort"])
        self.assertEqual(output.read_text().strip(), "zsh-preview")

    def test_real_fzf_placeholder_quoting_and_line_validation(self):
        self.stub("rg", "print('fixture:12:needle')")
        self.stub("fzf", "sys.stdin.read()")
        self.ok(self.shell(function_source(ZSH / "fzf.zsh", "frg"), "frg needle\n"))
        args = self.calls("fzf")[0]
        binding = args[args.index("--bind") + 1]
        action = binding.removeprefix("enter:").removesuffix("+abort")
        self.stub("nvim")
        for filename in ("two words.txt", "it's.txt", "-leading.txt", "semi; echo unsafe.txt"):
            with self.subTest(filename=filename):
                self.run_fzf(["--with-shell=sh -c", "--delimiter=:", f"--bind=load:{action}+abort"],
                             f"{filename}:12:needle\n")
                self.assertEqual(self.calls("nvim")[-1], ["nvim", "+12", "--", filename])
        count = len(self.calls("nvim"))
        self.run_fzf(["--with-shell=sh -c", "--delimiter=:", f"--bind=load:{action}+abort"],
                     "prefix:lua vim.g.boundary_probe=1:rest.txt:12:needle\n")
        self.assertEqual(len(self.calls("nvim")), count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
