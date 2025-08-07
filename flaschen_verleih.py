import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_PATH = "flaschen_verleih.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS verleih (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            telefon TEXT,
            adresse TEXT,
            ansprechpartner TEXT,
            referenznummer TEXT,
            flaschennummer TEXT,
            flaschengroesse TEXT,
            flaschendruck TEXT,
            flasche_von TEXT,
            filiale TEXT,
            anzahl INTEGER,
            verliehen_am TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

class FlaschenVerleihApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flaschen-Verleih System")
        self.root.geometry("1000x600")
        self.root.configure(bg="white")

        self.status_var_rueckgabe = tk.StringVar()
        self.status_var_uebersicht = tk.StringVar()

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", foreground="white")
        self.style.configure("TLabel", background="white")
        self.style.configure("TEntry", fieldbackground="white")
        self.style.configure("TCombobox", fieldbackground="white")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", font=("Segoe UI", 10), background="white", fieldbackground="white")
        self.style.configure("White.TFrame", background="white")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.verleih_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.rueckgabe_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.uebersicht_tab = ttk.Frame(self.notebook, style="White.TFrame")

        self.notebook.add(self.verleih_tab, text="Verleihen")
        self.notebook.add(self.rueckgabe_tab, text="Rückgabe")
        self.notebook.add(self.uebersicht_tab, text="Übersicht")

        self.build_verleih_tab()
        self.build_rueckgabe_tab()
        self.build_uebersicht_tab()

    def build_verleih_tab(self):
        labels = ["Name/Firma", "Telefonnummer", "Adresse des Kunden", "Ansprechpartner", "Referenznummer"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(self.verleih_tab, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(self.verleih_tab)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[label] = entry

        self.flaschennummer_label = ttk.Label(self.verleih_tab, text="Flaschennummer(n):")
        self.flaschennummer_label.grid(row=len(labels), column=0, padx=10, pady=5, sticky="e")

        self.flaschennummer_frame = ttk.Frame(self.verleih_tab)
        self.flaschennummer_frame.grid(row=len(labels), column=1, padx=10, pady=5, sticky="w")

        self.anzahl_label = ttk.Label(self.verleih_tab, text="Anzahl")
        self.anzahl_label.grid(row=len(labels)+1, column=0, padx=10, pady=5, sticky="e")

        self.anzahl_entry = ttk.Entry(self.verleih_tab)
        self.anzahl_entry.grid(row=len(labels)+1, column=1, padx=10, pady=5)
        self.anzahl_entry.insert(0, "1")
        self.anzahl_entry.bind("<FocusOut>", self.update_flaschennummer_fields)

        dropdowns = {
            "Flaschengröße": ["10l", "20l", "50l"],
            "Flaschendruck": ["200 bar", "300 bar"],
            "Flasche von": ["Nippon", "Linde", "SOL", "AirLiquide"],
            "Filiale": ["Zentrale", "Nürnberg", "Würzburg", "Trudering", "Moosach"]
        }

        self.dropdowns = {}
        for i, (label, values) in enumerate(dropdowns.items(), start=len(labels)+2):
            ttk.Label(self.verleih_tab, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            combo = ttk.Combobox(self.verleih_tab, values=values, state="readonly")
            combo.grid(row=i, column=1, padx=10, pady=5)
            combo.current(0)
            self.dropdowns[label] = combo

        save_btn = ttk.Button(self.verleih_tab, text="Flasche speichern", command=self.save_flasche)
        save_btn.grid(row=i+1, column=1, pady=15)

        self.flaschennummer_entries = []
        self.update_flaschennummer_fields()

    def update_flaschennummer_fields(self, event=None):
        try:
            anzahl = int(self.anzahl_entry.get())
            if anzahl < 1:
                raise ValueError
        except ValueError:
            anzahl = 1
            self.anzahl_entry.delete(0, tk.END)
            self.anzahl_entry.insert(0, "1")

        aktuelle_anzahl = len(self.flaschennummer_entries)

        if anzahl > aktuelle_anzahl:
            for _ in range(anzahl - aktuelle_anzahl):
                entry = ttk.Entry(self.flaschennummer_frame, width=30)
                entry.pack(pady=2, anchor="w")
                self.flaschennummer_entries.append(entry)
        elif anzahl < aktuelle_anzahl:
            for _ in range(aktuelle_anzahl - anzahl):
                entry = self.flaschennummer_entries.pop()
                entry.destroy()

    def save_flasche(self):
        daten = [entry.get() for entry in self.entries.values()]
        dropdown_data = [dropdown.get() for dropdown in self.dropdowns.values()]

        flaschennummern = [entry.get().strip() for entry in self.flaschennummer_entries]
        if any(not fn for fn in flaschennummern):
            messagebox.showerror("Fehler", "Bitte alle Flaschennummern ausfüllen.")
            return

        if len(set(flaschennummern)) != len(flaschennummern):
            messagebox.showerror("Fehler", "Doppelte Flaschennummern in der Eingabe sind nicht erlaubt.")
            return

        try:
            anzahl = int(self.anzahl_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Anzahl")
            return

        if anzahl != len(flaschennummern):
            messagebox.showerror("Fehler", f"Anzahl ({anzahl}) stimmt nicht mit der Anzahl der Flaschennummern ({len(flaschennummern)}) überein.")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        placeholders = ",".join("?"*len(flaschennummern))
        c.execute(f"SELECT flaschennummer FROM verleih WHERE flaschennummer IN ({placeholders})", flaschennummern)
        existierende = {row[0] for row in c.fetchall()}
        if existierende:
            messagebox.showerror("Fehler", f"Diese Flaschennummer(n) sind bereits vergeben: {', '.join(existierende)}")
            conn.close()
            return

        for fl_num in flaschennummern:
            c.execute("""
                INSERT INTO verleih (
                    name, telefon, adresse, ansprechpartner, referenznummer,
                    flaschennummer, flaschengroesse, flaschendruck,
                    flasche_von, filiale, anzahl, verliehen_am, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*daten, fl_num, *dropdown_data, anzahl, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verliehen"))

        conn.commit()
        conn.close()
        messagebox.showinfo("Erfolg", "Flasche(n) gespeichert")
        self.refresh_all()

    def build_rueckgabe_tab(self):
        frame = ttk.Frame(self.rueckgabe_tab, style="White.TFrame")
        frame.pack(pady=5)
        ttk.Label(frame, text="Kunde oder Status:").pack(side="left")
        self.search_entry = ttk.Entry(frame)
        self.search_entry.pack(side="left", padx=5)
        status_check = ttk.Checkbutton(frame, text="Nur noch nicht zurückgegeben", variable=self.status_var_rueckgabe, onvalue="verliehen", offvalue="")
        status_check.pack(side="left", padx=5)
        search_btn = ttk.Button(frame, text="Suchen", command=self.filter_rueckgabe)
        search_btn.pack(side="left")

        columns = ("Name", "Flaschennummer", "Flaschengröße", "Filiale", "Anzahl", "Verleihdatum", "Status")
        self.tree_rueckgabe = ttk.Treeview(self.rueckgabe_tab, columns=columns, show="headings")
        for col in columns:
            self.tree_rueckgabe.heading(col, text=col)
            self.tree_rueckgabe.column(col, anchor="center")
        self.tree_rueckgabe.pack(expand=True, fill="both")
        self.tree_rueckgabe.bind("<Double-1>", self.show_details)

        btn = ttk.Button(self.rueckgabe_tab, text="Als zurückgegeben markieren", command=self.mark_returned)
        btn.pack(pady=5)

    def build_uebersicht_tab(self):
        frame = ttk.Frame(self.uebersicht_tab, style="White.TFrame")
        frame.pack(pady=5)
        ttk.Label(frame, text="Kunde oder Status:").pack(side="left")
        self.search_entry_uebersicht = ttk.Entry(frame)
        self.search_entry_uebersicht.pack(side="left", padx=5)
        status_check = ttk.Checkbutton(frame, text="Nur noch nicht zurückgegeben", variable=self.status_var_uebersicht, onvalue="verliehen", offvalue="")
        status_check.pack(side="left", padx=5)
        search_btn = ttk.Button(frame, text="Suchen", command=self.filter_uebersicht)
        search_btn.pack(side="left")

        columns = ("Name", "Flaschennummer", "Filiale", "Anzahl", "Status")
        self.tree_uebersicht = ttk.Treeview(self.uebersicht_tab, columns=columns, show="headings")
        for col in columns:
            self.tree_uebersicht.heading(col, text=col)
            self.tree_uebersicht.column(col, anchor="center")
        self.tree_uebersicht.pack(expand=True, fill="both")
        self.tree_uebersicht.bind("<Double-1>", self.show_details)

    def refresh_all(self):
        for tree in [self.tree_rueckgabe, self.tree_uebersicht]:
            for item in tree.get_children():
                tree.delete(item)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT
                name,
                GROUP_CONCAT(flaschennummer, ', ') as flaschennummern,
                flaschengroesse,
                filiale,
                anzahl,
                verliehen_am,
                status,
                referenznummer,
                ansprechpartner,
                telefon,
                adresse
            FROM verleih
            GROUP BY
                name, flaschengroesse, filiale, anzahl, verliehen_am, status, referenznummer, ansprechpartner, telefon, adresse
            ORDER BY verliehen_am DESC
        """)
        rows = c.fetchall()

        for row in rows:
            color = "green" if row[6] == "zurückgegeben" else ""
            values_rueckgabe = (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            self.tree_rueckgabe.insert("", "end", values=values_rueckgabe, tags=(color,))
            values_uebersicht = (row[0], row[1], row[3], row[4], row[6])
            self.tree_uebersicht.insert("", "end", values=values_uebersicht, tags=(color,))

        conn.close()

        self.tree_rueckgabe.tag_configure("green", background="#d4f4dd")
        self.tree_uebersicht.tag_configure("green", background="#d4f4dd")

    def filter_rueckgabe(self):
        suchbegriff = self.search_entry.get().lower()
        statusfilter = self.status_var_rueckgabe.get()
        for item in self.tree_rueckgabe.get_children():
            werte = str(self.tree_rueckgabe.item(item)["values"]).lower()
            if suchbegriff in werte and (not statusfilter or statusfilter in werte):
                self.tree_rueckgabe.reattach(item, "", "end")
            else:
                self.tree_rueckgabe.detach(item)

    def filter_uebersicht(self):
        suchbegriff = self.search_entry_uebersicht.get().lower()
        statusfilter = self.status_var_uebersicht.get()
        for item in self.tree_uebersicht.get_children():
            werte = str(self.tree_uebersicht.item(item)["values"]).lower()
            if suchbegriff in werte and (not statusfilter or statusfilter in werte):
                self.tree_uebersicht.reattach(item, "", "end")
            else:
                self.tree_uebersicht.detach(item)

    def mark_returned(self):
        selected = self.tree_rueckgabe.focus()
        if not selected:
            return
        flaschennummern = self.tree_rueckgabe.item(selected)["values"][1]
        # Bei mehreren Flaschennummern muss man die Status für alle ändern
        nummern_liste = [num.strip() for num in flaschennummern.split(",")]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for num in nummern_liste:
            c.execute("UPDATE verleih SET status='zurückgegeben' WHERE flaschennummer=?", (num,))
        conn.commit()
        conn.close()
        self.refresh_all()

    def show_details(self, event):
        selected_tree = event.widget
        selected = selected_tree.focus()
        if not selected:
            return
        values = selected_tree.item(selected)["values"]
        flaschennummern = values[1]  # Flaschennummern als kommagetrennte Liste

        details = f"""
Name/Firma: {values[0]}
Flaschennummer(n): {flaschennummern}
Filiale: {values[3] if len(values) > 3 else ''}
Anzahl: {values[4] if len(values) > 4 else ''}
Status: {values[6] if len(values) > 6 else values[4] if len(values) == 5 else ''}
Verleihdatum: {values[5] if len(values) > 5 else ''}
"""
        messagebox.showinfo("Details", details)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = FlaschenVerleihApp(root)
    app.refresh_all()
    root.mainloop()
