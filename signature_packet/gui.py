"""Minimal Tkinter GUI: browse or drag-drop PDF/DOCX, build signature packet."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from signature_packet.engine import PacketOptions, build_signature_packet

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _HAS_DND = True
except ImportError:
    _HAS_DND = False


def _make_root():
    if _HAS_DND:
        return TkinterDnD.Tk()
    return tk.Tk()


def _parse_drop_paths(data: str) -> list[str]:
    # tkinterdnd2 gives brace-wrapped paths on some platforms
    raw = data.strip()
    if raw.startswith("{") and "}" in raw:
        out: list[str] = []
        i = 0
        while i < len(raw):
            if raw[i] == "{":
                j = raw.find("}", i + 1)
                if j == -1:
                    break
                out.append(raw[i + 1 : j])
                i = j + 1
            else:
                i += 1
        return [p for p in out if p]
    return [p for p in data.split() if p]


def _is_allowed(p: str) -> bool:
    return Path(p).suffix.lower() in {".pdf", ".docx", ".doc"}


class SignaturePacketGUI:
    def __init__(self) -> None:
        self.root = _make_root()
        self.root.title("Signature packet")
        self.root.minsize(420, 360)
        self.root.geometry("520x420")

        self._paths: list[str] = []
        self._busy = False

        main = ttk.Frame(self.root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="PDF / DOCX files").pack(anchor=tk.W)
        drop_hint = (
            "Drop files here (install tkinterdnd2 for drag-and-drop), "
            "or use Browse."
            if not _HAS_DND
            else "Drop files here or use Browse."
        )
        ttk.Label(main, text=drop_hint, font=("", 9)).pack(anchor=tk.W)

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(list_frame, height=8, yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.listbox.yview)

        if _HAS_DND:
            self.listbox.drop_target_register(DND_FILES)
            self.listbox.dnd_bind("<<Drop>>", self._on_drop)

        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="Browse…", command=self._browse).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_row, text="Remove", command=self._remove_selected).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_row, text="Clear", command=self._clear).pack(side=tk.LEFT)

        out_row = ttk.Frame(main)
        out_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(out_row, text="Output PDF").pack(anchor=tk.W)
        out_inner = ttk.Frame(out_row)
        out_inner.pack(fill=tk.X, pady=2)
        self.output_var = tk.StringVar(value=str(Path.cwd() / "signature_packet.pdf"))
        ttk.Entry(out_inner, textvariable=self.output_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(out_inner, text="Save as…", command=self._browse_output).pack(
            side=tk.LEFT
        )

        self.title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main, text="Prepend title page", variable=self.title_var).pack(
            anchor=tk.W, pady=(4, 0)
        )

        self.run_btn = ttk.Button(main, text="Build packet", command=self._run)
        self.run_btn.pack(fill=tk.X, pady=(8, 4))

        ttk.Label(main, text="Log").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(main, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _log_line(self, msg: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _sync_listbox(self) -> None:
        self.listbox.delete(0, tk.END)
        for p in self._paths:
            self.listbox.insert(tk.END, p)

    def _add_paths(self, paths: list[str]) -> None:
        for p in paths:
            p = p.strip()
            if not p or not Path(p).is_file():
                continue
            if not _is_allowed(p):
                self._log_line(f"Skipped (not PDF/DOCX): {p}")
                continue
            rp = str(Path(p).resolve())
            if rp not in self._paths:
                self._paths.append(rp)
        self._sync_listbox()

    def _on_drop(self, event) -> None:
        for p in _parse_drop_paths(event.data):
            self._add_paths([p])

    def _browse(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select documents",
            filetypes=[
                ("Documents", "*.pdf *.docx *.doc"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx *.doc"),
                ("All", "*.*"),
            ],
        )
        if files:
            self._add_paths(list(files))

    def _browse_output(self) -> None:
        p = filedialog.asksaveasfilename(
            title="Save signature packet as",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if p:
            self.output_var.set(p)

    def _remove_selected(self) -> None:
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            if 0 <= i < len(self._paths):
                del self._paths[i]
        self._sync_listbox()

    def _clear(self) -> None:
        self._paths.clear()
        self._sync_listbox()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.run_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)

    def _run(self) -> None:
        if self._busy:
            return
        if not self._paths:
            messagebox.showinfo("Signature packet", "Add at least one PDF or DOCX file.")
            return
        out = self.output_var.get().strip()
        if not out:
            messagebox.showinfo("Signature packet", "Choose an output PDF path.")
            return

        opts = PacketOptions(
            output=out,
            title_page=self.title_var.get(),
            verbose=True,
        )

        self._set_busy(True)
        self._log_line("Starting…")

        def work() -> None:
            def log_ui(m: str) -> None:
                self.root.after(0, lambda: self._log_line(m))

            def warn_ui(m: str) -> None:
                self.root.after(0, lambda: self._log_line(m))

            try:
                code, _path = build_signature_packet(
                    list(self._paths),
                    opts,
                    log=log_ui,
                    warn=warn_ui,
                )
            except Exception as e:
                err = str(e)
                self.root.after(
                    0,
                    lambda e=err: self._finish_run(False, f"Error: {e}"),
                )
                return

            msg = None if code == 0 else "No signature pages found in any input."
            self.root.after(
                0,
                lambda c=code, m=msg: self._finish_run(c == 0, m),
            )

        threading.Thread(target=work, daemon=True).start()

    def _finish_run(self, ok: bool, err_msg: str | None) -> None:
        self._set_busy(False)
        if ok:
            messagebox.showinfo("Signature packet", "Done.")
        elif err_msg:
            self._log_line(err_msg)
            messagebox.showerror("Signature packet", err_msg)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        SignaturePacketGUI().run()
    except tk.TclError as e:
        print(
            "Tkinter failed to start. On Debian/Ubuntu install: sudo apt install python3-tk",
            file=__import__("sys").stderr,
        )
        print(e, file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
