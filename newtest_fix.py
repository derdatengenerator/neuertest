import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flaschen_verleih.db")

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS bestand (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filiale TEXT,
            flaschengroesse TEXT,
            flaschendruck TEXT,
            bestand INTEGER
        )
    """)
    filialen = ["Zentrale", "Nürnberg", "Würzburg", "Trudering", "Moosach"]
    groessen = ["10l", "20l", "50l"]
    druecke = ["200 bar", "300 bar"]
    for f in filialen:
        for g in groessen:
            for d in druecke:
                c.execute(
                    "SELECT COUNT(*) FROM bestand WHERE filiale=? AND flaschengroesse=? AND flaschendruck=?",
                    (f, g, d),
                )
                if c.fetchone()[0] == 0:
                    c.execute(
                        "INSERT INTO bestand (filiale, flaschengroesse, flaschendruck, bestand) VALUES (?, ?, ?, 0)",
                        (f, g, d),
                    )
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
        self.bestand_tab = ttk.Frame(self.notebook, style="White.TFrame")

        self.notebook.add(self.verleih_tab, text="Verleihen")
        self.notebook.add(self.rueckgabe_tab, text="Rückgabe")
        self.notebook.add(self.uebersicht_tab, text="Übersicht")
        self.notebook.add(self.bestand_tab, text="Bestand")

        self.build_verleih_tab()
        self.build_rueckgabe_tab()
        self.build_uebersicht_tab()
        self.build_bestand_tab()
        self.refresh_all()

    def build_verleih_tab(self):
        labels = ["Name/Firma", "Telefonnummer", "Adresse des Kunden", "Ansprechpartner", "Referenznummer"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(self.verleih_tab, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(self.verleih_tab)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.entries[label] = entry

        self.flaschennummer_label = ttk.Label(self.verleih_tab, text="Flaschennummer(n):")
        self.flaschennummer_label.grid(row=len(labels), column=0, padx=10, pady=5, sticky="e")

        self.flaschennummer_frame = ttk.Frame(self.verleih_tab, style="White.TFrame")
        self.flaschennummer_frame.grid(row=len(labels), column=1, padx=10, pady=5, sticky="w")

        self.anzahl_label = ttk.Label(self.verleih_tab, text="Anzahl")
        self.anzahl_label.grid(row=len(labels)+1, column=0, padx=10, pady=5, sticky="e")

        self.anzahl_entry = ttk.Entry(self.verleih_tab)
        self.anzahl_entry.grid(row=len(labels)+1, column=1, padx=10, pady=5, sticky="ew")
        self.anzahl_entry.insert(0, "1")
        self.anzahl_entry.bind("<FocusOut>", self.update_flaschennummer_fields)
        self.anzahl_entry.bind("<Return>", self.update_flaschennummer_fields)

        dropdown_options = {
            "Flaschengröße": ["10l", "20l", "50l"],
            "Flaschendruck": ["200 bar", "300 bar"],
            "Flasche von": ["Linde", "Air Liquide", "Eigen"],
            "Filiale": ["Zentrale", "Nürnberg", "Würzburg", "Trudering", "Moosach"]
        }
        self.dropdowns = {}
        start_row = len(labels) + 2
        for i, (label, values) in enumerate(dropdown_options.items()):
            ttk.Label(self.verleih_tab, text=label).grid(row=start_row + i, column=0, padx=10, pady=5, sticky="e")
            combo = ttk.Combobox(self.verleih_tab, values=values, state="readonly")
            combo.grid(row=start_row + i, column=1, padx=10, pady=5, sticky="ew")
            combo.current(0)
            self.dropdowns[label] = combo

        save_btn = ttk.Button(self.verleih_tab, text="Speichern", command=self.verleihen)
        save_btn.grid(row=start_row + len(dropdown_options), column=1, pady=20)

        self.flaschennummer_entries = []
        self.update_flaschennummer_fields()

    def update_flaschennummer_fields(self, event=None):
        for entry in self.flaschennummer_entries:
            entry.destroy()
        self.flaschennummer_entries.clear()
        try:
            anzahl = int(self.anzahl_entry.get())
        except ValueError:
            anzahl = 0
        for i in range(anzahl):
            entry = ttk.Entry(self.flaschennummer_frame, width=15)
            entry.pack(pady=2, anchor="w")
            self.flaschennummer_entries.append(entry)

    def verleihen(self):
        daten = [self.entries[label].get() for label in ["Name/Firma", "Telefonnummer", "Adresse des Kunden", "Ansprechpartner", "Referenznummer"]]
        dropdown_data = [self.dropdowns[label].get() for label in ["Flaschengröße", "Flaschendruck", "Flasche von", "Filiale"]]
        
        try:
            anzahl = int(self.anzahl_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Anzahl muss eine gültige Zahl sein.")
            return

        flaschennummern = [entry.get() for entry in self.flaschennummer_entries if entry.get()]

        if any(not d for d in daten) or any(not d for d in dropdown_data):
            messagebox.showerror("Fehler", "Bitte alle Felder ausfüllen.")
            return

        if not flaschennummern:
            messagebox.showerror("Fehler", "Bitte Flaschennummer(n) eingeben.")
            return
        
        if anzahl != len(flaschennummern):
            messagebox.showerror("Fehler", f"Anzahl ({anzahl}) stimmt nicht mit der Anzahl der Flaschennummern ({len(flaschennummern)}) überein.")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        placeholders = ",".join("?"*len(flaschennummern))
        c.execute(f"SELECT flaschennummer FROM verleih WHERE flaschennummer IN ({placeholders}) AND status = 'verliehen'", flaschennummern)
        existierende = {row[0] for row in c.fetchall()}
        if existierende:
            messagebox.showerror("Fehler", f"Diese Flaschennummer(n) sind bereits verliehen: {', '.join(existierende)}")
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
        self.update_stock(
            self.dropdowns["Filiale"].get(),
            self.dropdowns["Flaschengröße"].get(),
            self.dropdowns["Flaschendruck"].get(),
            -anzahl,
        )
        messagebox.showinfo("Erfolg", "Flasche(n) erfolgreich verliehen.")
        self.refresh_all()
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.anzahl_entry.delete(0, tk.END)
        self.anzahl_entry.insert(0, "1")
        self.update_flaschennummer_fields()


    def build_rueckgabe_tab(self):
        frame = ttk.Frame(self.rueckgabe_tab, style="White.TFrame")
        frame.pack(pady=5, fill="x", padx=10)
        ttk.Label(frame, text="Suche:").pack(side="left", padx=(0,5))
        self.search_entry = ttk.Entry(frame)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        status_check = ttk.Checkbutton(frame, text="Nur nicht zurückgegeben", variable=self.status_var_rueckgabe, onvalue="verliehen", offvalue="")
        status_check.pack(side="left", padx=5)
        search_btn = ttk.Button(frame, text="Filtern", command=self.filter_rueckgabe)
        search_btn.pack(side="left")

        columns = ("Name", "Flaschennummer", "Flaschengröße", "Filiale", "Anzahl", "Verleihdatum", "Status")
        self.tree_rueckgabe = ttk.Treeview(self.rueckgabe_tab, columns=columns, show="headings")
        for col in columns:
            self.tree_rueckgabe.heading(col, text=col)
            self.tree_rueckgabe.column(col, anchor="center", width=120)
        self.tree_rueckgabe.pack(expand=True, fill="both", padx=10, pady=5)
        self.tree_rueckgabe.bind("<Double-1>", self.show_details)

        btn = ttk.Button(self.rueckgabe_tab, text="Als zurückgegeben markieren", command=self.mark_returned)
        btn.pack(pady=10)

    def build_uebersicht_tab(self):
        frame = ttk.Frame(self.uebersicht_tab, style="White.TFrame")
        frame.pack(pady=5, fill="x", padx=10)
        ttk.Label(frame, text="Suche:").pack(side="left", padx=(0,5))
        self.search_entry_uebersicht = ttk.Entry(frame)
        self.search_entry_uebersicht.pack(side="left", padx=5, fill="x", expand=True)
        status_check = ttk.Checkbutton(frame, text="Nur nicht zurückgegeben", variable=self.status_var_uebersicht, onvalue="verliehen", offvalue="")
        status_check.pack(side="left", padx=5)
        search_btn = ttk.Button(frame, text="Filtern", command=self.filter_uebersicht)
        search_btn.pack(side="left")

        columns = ("Name", "Flaschennummer", "Filiale", "Anzahl", "Status")
        self.tree_uebersicht = ttk.Treeview(self.uebersicht_tab, columns=columns, show="headings")
        for col in columns:
            self.tree_uebersicht.heading(col, text=col)
            self.tree_uebersicht.column(col, anchor="center", width=150)
        self.tree_uebersicht.pack(expand=True, fill="both", padx=10, pady=5)
        self.tree_uebersicht.bind("<Double-1>", self.show_details)

    def build_bestand_tab(self):
        frame = ttk.Frame(self.bestand_tab, style="White.TFrame")
        frame.pack(pady=20, padx=10)
        ttk.Label(frame, text="Filiale:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.bestand_filiale = ttk.Combobox(
            frame,
            values=["Zentrale", "Nürnberg", "Würzburg", "Trudering", "Moosach"],
            state="readonly",
        )
        self.bestand_filiale.grid(row=0, column=1, padx=5, pady=5)
        self.bestand_filiale.current(0)

        ttk.Label(frame, text="Flaschengröße:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.bestand_groesse = ttk.Combobox(frame, values=["10l", "20l", "50l"], state="readonly")
        self.bestand_groesse.grid(row=1, column=1, padx=5, pady=5)
        self.bestand_groesse.current(0)

        ttk.Label(frame, text="Flaschendruck:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.bestand_druck = ttk.Combobox(frame, values=["200 bar", "300 bar"], state="readonly")
        self.bestand_druck.grid(row=2, column=1, padx=5, pady=5)
        self.bestand_druck.current(0)

        ttk.Label(frame, text="Neuer Bestand:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.bestand_entry = ttk.Entry(frame)
        self.bestand_entry.grid(row=3, column=1, padx=5, pady=5)

        btn = ttk.Button(frame, text="Bestand setzen", command=self.set_bestand)
        btn.grid(row=4, column=1, pady=10, sticky="e")

        columns = ("Filiale", "Flaschengröße", "Flaschendruck", "Bestand")
        self.tree_bestand = ttk.Treeview(self.bestand_tab, columns=columns, show="headings")
        for col in columns:
            self.tree_bestand.heading(col, text=col)
            self.tree_bestand.column(col, anchor="center")
        self.tree_bestand.pack(expand=True, fill="both", padx=10, pady=10)
        self.refresh_bestand()

    def refresh_bestand(self):
        for item in self.tree_bestand.get_children():
            self.tree_bestand.delete(item)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT filiale, flaschengroesse, flaschendruck, bestand FROM bestand ORDER BY filiale, flaschengroesse, flaschendruck"
        )
        rows = c.fetchall()
        conn.close()
        for row in rows:
            self.tree_bestand.insert("", "end", values=row)

    def set_bestand(self):
        filiale = self.bestand_filiale.get()
        groesse = self.bestand_groesse.get()
        druck = self.bestand_druck.get()
        try:
            menge = int(self.bestand_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiger Bestandswert. Bitte eine Zahl eingeben.")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE bestand SET bestand=? WHERE filiale=? AND flaschengroesse=? AND flaschendruck=?",
            (menge, filiale, groesse, druck),
        )
        conn.commit()
        conn.close()
        self.bestand_entry.delete(0, tk.END)
        self.refresh_bestand()

    def update_stock(self, filiale, groesse, druck, delta):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE bestand SET bestand = bestand + ? WHERE filiale=? AND flaschengroesse=? AND flaschendruck=?",
            (delta, filiale, groesse, druck),
        )
        conn.commit()
        conn.close()
        self.refresh_bestand()

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
                id
            FROM verleih
            GROUP BY
                name, flaschengroesse, filiale, anzahl, verliehen_am, status, referenznummer, ansprechpartner, telefon, adresse
            ORDER BY verliehen_am DESC
        """)
        rows = c.fetchall()

        for row in rows:
            color_tag = "green" if row[6] == "zurückgegeben" else "red"
            values_rueckgabe = (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            self.tree_rueckgabe.insert("", "end", values=values_rueckgabe, tags=(color_tag,), iid=row[7])
            values_uebersicht = (row[0], row[1], row[3], row[4], row[6])
            self.tree_uebersicht.insert("", "end", values=values_uebersicht, tags=(color_tag,), iid=row[7])

        conn.close()

        self.tree_rueckgabe.tag_configure("green", background="#d4edda")
        self.tree_uebersicht.tag_configure("green", background="#d4edda")
        self.tree_rueckgabe.tag_configure("red", background="#f8d7da")
        self.tree_uebersicht.tag_configure("red", background="#f8d7da")
        self.refresh_bestand()

    def filter_rueckgabe(self):
        self.filter_tree(self.tree_rueckgabe, self.search_entry.get(), self.status_var_rueckgabe.get())

    def filter_uebersicht(self):
        self.filter_tree(self.tree_uebersicht, self.search_entry_uebersicht.get(), self.status_var_uebersicht.get())
        
    def filter_tree(self, tree, search_term, status_filter):
        self.refresh_all() # First, show all items
        search_term = search_term.lower()
        for item_id in tree.get_children():
            item = tree.item(item_id)
            values = item['values']
            status = values[-1]
            
            # Check for status filter match
            status_match = (not status_filter) or (status_filter == status)
            
            # Check for search term match
            search_match = search_term in str(values).lower()
            
            if not (status_match and search_match):
                tree.detach(item_id)

    def mark_returned(self):
        selected = self.tree_rueckgabe.focus()
        if not selected:
            messagebox.showwarning("Achtung", "Bitte einen Eintrag auswählen.")
            return
            
        values = self.tree_rueckgabe.item(selected)["values"]
        if values[6] == "zurückgegeben":
            messagebox.showinfo("Info", "Dieser Eintrag ist bereits als zurückgegeben markiert.")
            return

        flaschennummern = values[1]
        nummern_liste = [num.strip() for num in flaschennummern.split(",")]
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for num in nummern_liste:
            c.execute(
                "SELECT filiale, flaschengroesse, flaschendruck FROM verleih WHERE flaschennummer=?",
                (num,),
            )
            info = c.fetchone()
            if info:
                filiale, groesse, druck = info
                self.update_stock(filiale, groesse, druck, 1) # Increase stock by 1 for each bottle
            c.execute("UPDATE verleih SET status='zurückgegeben' WHERE flaschennummer=?", (num,))
        conn.commit()
        conn.close()
        self.refresh_all()
        messagebox.showinfo("Erfolg", f"{len(nummern_liste)} Flasche(n) als zurückgegeben markiert.")

    def show_details(self, event):
        selected_tree = event.widget
        selected = selected_tree.focus()
        if not selected:
            return
        
        values = selected_tree.item(selected)["values"]
        flaschennummern_str = values[1]
        
        first_flaschennummer = flaschennummern_str.split(',')[0].strip()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, telefon, adresse, ansprechpartner, referenznummer, flaschengroesse, flaschendruck, flasche_von, filiale, anzahl, verliehen_am, status FROM verleih WHERE flaschennummer=?", (first_flaschennummer,))
        details_data = c.fetchone()
        conn.close()

        if not details_data:
            messagebox.showerror("Fehler", f"Details für Flasche {first_flaschennummer} nicht in der Datenbank gefunden.")
            return

        details_map = {
            "Name/Firma": details_data[0], "Telefonnummer": details_data[1], "Adresse des Kunden": details_data[2],
            "Ansprechpartner": details_data[3], "Referenznummer": details_data[4], "Flaschengröße": details_data[5],
            "Flaschendruck": details_data[6], "Flasche von": details_data[7], "Filiale": details_data[8],
            "Anzahl": details_data[9], "Verliehen am": details_data[10], "Status": details_data[11]
        }

        details_string = f"""KUNDENDETAILS
------------------------------------
Name/Firma: {details_map['Name/Firma']}
Telefonnummer: {details_map['Telefonnummer']}
Adresse: {details_map['Adresse des Kunden']}
Ansprechpartner: {details_map['Ansprechpartner']}
Referenznummer: {details_map['Referenznummer']}

FLASCHENDETAILS
------------------------------------
Flaschennummer(n): {flaschennummern_str}
Anzahl: {details_map['Anzahl']}
Flaschengröße: {details_map['Flaschengröße']}
Flaschendruck: {details_map['Flaschendruck']}
Flasche von: {details_map['Flasche von']}
Filiale: {details_map['Filiale']}
Verliehen am: {details_map['Verliehen am']}
Status: {details_map['Status']}
"""
        messagebox.showinfo("Details zum Verleih", details_string)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = FlaschenVerleihApp(root)
    root.mainloop()