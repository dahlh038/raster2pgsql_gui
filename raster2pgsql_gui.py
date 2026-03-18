import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import json
import sys
import threading

PROFILE_FILE = "raster_loader_profiles.json"

class Raster2PgsqlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PostGIS Raster Loader")
        self.root.geometry("850x650")

        # ================= Main Canvas for Scroll =================
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        main_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        main_scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=main_scrollbar.set)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # ================= Top Section =================
        self.create_top_widgets(self.scrollable_frame)

        # ================= Log Section =================
        log_frame = ttk.LabelFrame(self.scrollable_frame, text="Log")
        log_frame.pack(fill="x", padx=5, pady=5)

        self.log = tk.Text(log_frame, wrap="none", height=15)
        self.log.pack(side="left", fill="both", expand=True)

        log_scroll_y = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_scroll_y.pack(side="right", fill="y")
        log_scroll_x = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log.xview)
        log_scroll_x.pack(side="bottom", fill="x")

        self.log.config(yscrollcommand=log_scroll_y.set, xscrollcommand=log_scroll_x.set)

        # ================= Bottom Buttons =================
        bottom_frame = ttk.Frame(root, padding=5)
        bottom_frame.pack(side="bottom", fill="x")
        self.progress = ttk.Progressbar(bottom_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=2)

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Preview SQL", command=self.preview_sql).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Run", command=self.run).pack(side="left", padx=5)

    # ---------------- Top Widgets ----------------
    def create_top_widgets(self, parent):
        # ---- Input Raster ----
        input_frame = ttk.LabelFrame(parent, text="Input Raster")
        input_frame.pack(fill="x", pady=2)
        self.file_entry = ttk.Entry(input_frame)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)

        # ---- Connection ----
        conn_frame = ttk.LabelFrame(parent, text="Connection")
        conn_frame.pack(fill="x", pady=2)
        self.host = self._entry(conn_frame, "Host", "localhost")
        self.port = self._entry(conn_frame, "Port", "5432")
        self.db = self._entry(conn_frame, "Database")
        self.user = self._entry(conn_frame, "User")
        self.password = self._entry(conn_frame, "Password", show="*")
        prof_frame = ttk.Frame(conn_frame)
        prof_frame.pack(fill="x", pady=2)
        ttk.Button(prof_frame, text="Save Profile", command=self.save_profile).pack(side="left")
        ttk.Button(prof_frame, text="Load Profile", command=self.load_profile).pack(side="left")

        # ---- Options ----
        opt_frame = ttk.LabelFrame(parent, text="Options")
        opt_frame.pack(fill="x", pady=2)
        self.schema = self._entry(opt_frame, "Schema", "public")
        self.table = self._entry(opt_frame, "Table")
        self.srid = self._entry(opt_frame, "SRID", "4326")
        self.tile = self._entry(opt_frame, "Tile Size", "100x100")
        ttk.Button(opt_frame, text="Auto-detect SRID", command=self.detect_srid).pack(pady=2)

        self.flag_I = tk.BooleanVar(value=True)
        self.flag_C = tk.BooleanVar(value=True)
        self.flag_M = tk.BooleanVar(value=True)
        self.flag_F = tk.BooleanVar()
        self.flag_k = tk.BooleanVar()
        self.flag_n = tk.BooleanVar()
        self.flag_l = tk.BooleanVar()

        for text, var in [
            ("Create index (-I)", self.flag_I),
            ("Constraints (-C)", self.flag_C),
            ("VACUUM (-M)", self.flag_M),
            ("Filename col (-F)", self.flag_F),
            ("Keep empty (-k)", self.flag_k),
            ("No constraints (-n)", self.flag_n),
            ("Overviews (-l)", self.flag_l)
        ]:
            ttk.Checkbutton(opt_frame, text=text, variable=var).pack(anchor="w")

        self.mode = tk.StringVar(value="-c")
        for text, val in [("Create", "-c"), ("Append", "-a"), ("Drop", "-d")]:
            ttk.Radiobutton(opt_frame, text=text, variable=self.mode, value=val).pack(anchor="w")

        self.output_mode = tk.StringVar(value="db")
        ttk.Radiobutton(opt_frame, text="To DB", variable=self.output_mode, value="db").pack(anchor="w")
        ttk.Radiobutton(opt_frame, text="To SQL file", variable=self.output_mode, value="file").pack(anchor="w")
        self.sql_file = ttk.Entry(opt_frame)
        self.sql_file.pack(fill="x")
        ttk.Button(opt_frame, text="Browse SQL", command=self.browse_sql).pack(pady=2)

    # ---------------- Helper Methods ----------------
    def _entry(self, parent, label, default="", show=None):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=1)
        ttk.Label(frame, text=label, width=18).pack(side="left")
        e = ttk.Entry(frame, show=show)
        e.insert(0, default)
        e.pack(side="left", fill="x", expand=True)
        return e

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def browse_sql(self):
        path = filedialog.asksaveasfilename(defaultextension=".sql")
        if path:
            self.sql_file.delete(0, tk.END)
            self.sql_file.insert(0, path)

    def detect_srid(self):
        try:
            result = subprocess.run(["gdalinfo", self.file_entry.get()], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "EPSG" in line:
                    srid = ''.join(filter(str.isdigit, line))
                    self.srid.delete(0, tk.END)
                    self.srid.insert(0, srid)
                    return
            messagebox.showinfo("SRID", "Could not detect SRID")
        except:
            messagebox.showerror("Error", "gdalinfo not found")

    def save_profile(self):
        data = {"host": self.host.get(), "port": self.port.get(), "db": self.db.get(), "user": self.user.get()}
        with open(PROFILE_FILE, "w") as f:
            json.dump(data, f)
        messagebox.showinfo("Saved", "Profile saved")

    def load_profile(self):
        if not os.path.exists(PROFILE_FILE): return
        with open(PROFILE_FILE) as f:
            data = json.load(f)
        self.host.delete(0, tk.END); self.host.insert(0, data.get("host", ""))
        self.port.delete(0, tk.END); self.port.insert(0, data.get("port", ""))
        self.db.delete(0, tk.END); self.db.insert(0, data.get("db", ""))
        self.user.delete(0, tk.END); self.user.insert(0, data.get("user", ""))

    def build_cmd(self):
        cmd = ["raster2pgsql", self.mode.get(), "-s", self.srid.get(), "-t", self.tile.get()]
        if self.flag_I.get(): cmd.append("-I")
        if self.flag_C.get(): cmd.append("-C")
        if self.flag_M.get(): cmd.append("-M")
        if self.flag_F.get(): cmd.append("-F")
        if self.flag_k.get(): cmd.append("-k")
        if self.flag_n.get(): cmd.append("-n")
        if self.flag_l.get(): cmd += ["-l", "2,4,8"]
        cmd += [self.file_entry.get(), f"{self.schema.get()}.{self.table.get()}"]
        return cmd

    def preview_sql(self):
        try:
            result = subprocess.run(self.build_cmd(), capture_output=True, text=True)
            self.log.insert(tk.END, result.stdout + "\n")
            self.log.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- Fast Log Run Function ----------------
    def run(self):
        def task():
            self.progress.start()
            raster_file = self.file_entry.get()
            table_name = f"{self.schema.get()}.{self.table.get()}"
            mode = self.mode.get()
            tile_size = self.tile.get()

            # Log start info
            self.log.insert(tk.END, f"Importing raster with configuration:\n"
                                     f"File: {raster_file}\n"
                                     f"Table: {table_name}\n"
                                     f"Mode: {mode}, Tile: {tile_size}\n")
            self.log.see(tk.END)

            cmd = self.build_cmd()

            try:
                if self.output_mode.get() == "file":
                    with open(self.sql_file.get(), "w") as f:
                        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True, shell=False)
                    self.log.insert(tk.END, "SQL file written.\n")
                else:
                    env = os.environ.copy()
                    env["PGPASSWORD"] = self.password.get()
                    psql_cmd = ["psql",
                                "-h", self.host.get(),
                                "-p", self.port.get(),
                                "-U", self.user.get(),
                                "-d", self.db.get()]
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    # Run without showing all SQL
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   shell=False, env=env, creationflags=creationflags)
                    subprocess.run(psql_cmd, input='', shell=False, env=env, creationflags=creationflags)

                    self.log.insert(tk.END, "Raster import completed.\n")

                self.progress.stop()
                self.log.see(tk.END)
                messagebox.showinfo("Done", "Import complete")

            except Exception as e:
                self.progress.stop()
                self.log.insert(tk.END, f"Error: {str(e)}\n")
                self.log.see(tk.END)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = Raster2PgsqlGUI(root)
    root.mainloop()