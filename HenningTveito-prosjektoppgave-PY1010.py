"""
Kode skrevet av Henning Tveito, 2026 03 16
Arbeidskrav 3 - individuell prosjektoppgave - elevstatistikk
PY1010 Introduksjon til Python
"""

# -*- coding: utf-8 -*-
import json
import os
import sys
import re
import logging
import subprocess
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



"""
Logging. Programmets dagbok over hendelser. 
"""
logging.basicConfig(
    filename="elevstatistikk.log",  # Logg tilknyttet JSON-datafilen skal registreres i elevstatistikk.log.
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger()

logger.info("Program startet.")



"""
JSON-datafil
"""
DATA_FILE = "data.json"  # dette er JSON-filen, som lagrer dataen som legges inn i programmet. Filplasseringen kan endres i programmet, eller hardkodes her.
valgt_aar = None


def les_data():
    """Leser JSON-data fra fil eller lager tom fil hvis mangler."""
    if not os.path.exists(DATA_FILE):
        logger.warning(f"{DATA_FILE} manglet – oppretter ny fil.")
        skriv_data({})
        return {}

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            logger.info("Data lastet fra JSON.")
            return data
    except json.JSONDecodeError:
        logger.error("JSON-filen er korrupt! Reinitialiserer.")
        skriv_data({})
        return {}


def skriv_data(data):
    """Lagrer data til JSON."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("Data skrevet til JSON-fil.")
    except Exception as e:
        logger.exception("Kunne ikke skrive til datafil.")
        messagebox.showerror("Feil", f"Kunne ikke skrive datafil:\n{e}")


def sorter_skolear(aarsliste):
    """Sorterer skoleår basert på første årstall."""
    try:
        return sorted(aarsliste, key=lambda x: int(x.split("/")[0]))
    except:
        logger.warning("Kunne ikke sortere – fallback brukes.")
        return sorted(aarsliste)



"""
Funksjon som sjekker om skoleåret er gyldig. Tvinger brukeren til å skrive inn året etter etter standard som 2025/2026.
"""
def valid_skoLEAR(s):
 
    if not re.match(r"^\d{4}/\d{4}$", s):
        return False

    år1, år2 = map(int, s.split("/"))
    return år2 == år1 + 1



"""
Sektordiagrammet
"""
def _autopct_formatter(values):  
    total = sum(values)

    def fmt(pct):
        count = int(round(pct / 100 * total))
        return f"{count} ({pct:.1f}%)"

    return fmt  # her returneres resultatet av de to funksjonene og gir tekst og prosentverdi til sektordiagrammet.


def oppdater_sektordiagram(frame, data, aar):  # denne funksjonen sjekker innholdet i diagrammet og tømmer det for å oppdatere det med ny informasjon.
    for w in frame.winfo_children():
        w.destroy()

    if aar not in data:
        ctk.CTkLabel(frame, text="Ingen data for dette skoleåret.").pack(pady=20)
        return

    d = data[aar]  
    elever = d["elever"]
    values = [d["laerlinger"], d["pabygg"], d["annet"]]  # dette er verdiene i JSON-fila
    labels = ["Lærlinger", "Påbygg", "Annet"]  # Dette er taggene/navnelappene i diagrammet.
    colors = ["tab:green", "tab:red", "tab:blue"]  # dette er fargene for å skille diagramfargene fra hverandre.

    ctk.CTkLabel(
        frame, text=f"{aar} – Totalt antall elever: {elever}", font=("Arial", 24)  # Overskriften for oversikt over diagrammet per år.
    ).pack(pady=(10, 5))

    if sum(values) == 0:
        ctk.CTkLabel(frame, text="Ingen fordeling å vise.").pack(pady=20)
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))  # figuren og aksene
    fig.subplots_adjust(right=0.70)

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        autopct=_autopct_formatter(values),
        pctdistance=0.68,
        startangle=90,
        counterclock=False,
        textprops={"fontsize": 10},
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )


    ax.legend(
        wedges,
        labels,
        title="Kategorier",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        frameon=False,
    )

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)



"""
Knapper for å vise skoleår, etter hvert som de legges til/slettes/endres
"""
def vis_aar(aar):
    global valgt_aar
    valgt_aar = aar
    logger.info(f"Viser skoleår {aar}")
    oppdater_sektordiagram(graf_container, data, valgt_aar)


def oppdater_aarsknapper():
    for w in aarsknapper_frame.winfo_children():
        w.destroy()

    if not data:
        ctk.CTkLabel(aarsknapper_frame, text="Ingen skoleår registrert").pack()
        return

    aar_sortert = sorter_skolear(list(data.keys()))

    for aar in aar_sortert:
        ctk.CTkButton(
            aarsknapper_frame,
            text=aar,
            width=120,
            command=lambda y=aar: vis_aar(y),
        ).pack(side="left", padx=5)

    global valgt_aar
    if valgt_aar not in data:
        valgt_aar = aar_sortert[-1]

    vis_aar(valgt_aar)



"""
Knapper i grensesnittet, med funksjoner som leser og skriver data til JSON-filen
"""
def legg_til_eller_endre():  # her kan man legge til eller endre registrert data.
    global data
    skolear = entry_aar.get().strip()

    if not valid_skoLEAR(skolear):
        messagebox.showerror(
            "Feil", "Ugyldig skoleår.\nSkriv hele årstall i formatet 2025/2026."
        )
        return

    try:
        elever = int(entry_elever.get())
        laerlinger = int(entry_laerlinger.get())
        pabygg = int(entry_pabygg.get())
        annet = int(entry_annet.get())
    except ValueError:
        messagebox.showerror("Feil", "Alle feltene må være heltall.")
        return

    if laerlinger + pabygg + annet != elever:
        messagebox.showerror(
            "Feil", "Summen av Lærlinger + Påbygg + Annet må være lik totalt antall elever."  # sjekker at verdien er lik, og gir brukeren tilbakemelding
        )
        return

    data[skolear] = {
        "elever": elever,
        "laerlinger": laerlinger,
        "pabygg": pabygg,
        "annet": annet,
    }

    skriv_data(data)
    oppdater_aarsknapper()
    logger.info(f"Data for {skolear} lagret.")
    messagebox.showinfo("OK", f"Data for {skolear} lagret.")


def slett_data():  # funksjon for å slette skoleår.
    global data
    skolear = entry_aar.get().strip()

    if skolear in data:
        del data[skolear]
        skriv_data(data)
        oppdater_aarsknapper()
        logger.info(f"{skolear} slettet.")
        messagebox.showinfo("OK", f"{skolear} slettet.")
    else:
        messagebox.showerror("Feil", "Skoleåret finnes ikke.")


def velg_lagringsplass():  # mulighet til å endre lagringsplass for JSON-fila. Nullstilles når programmet lukkes.
    global DATA_FILE
    filsti = filedialog.asksaveasfilename(
        defaultextension=".json", filetypes=[("JSON filer", "*.json")]
    )
    if filsti:
        DATA_FILE = filsti
        skriv_data(data)
        label_path.configure(text=f"Lagringsplass: {os.path.abspath(DATA_FILE)}")
        logger.info(f"Lagringsplass endret til {DATA_FILE}")


def åpne_mappe():  # funksjon for å åpne mappen der JSON-fila ligger lagret.
    mappe = os.path.dirname(os.path.abspath(DATA_FILE))
    if sys.platform == "win32":
        subprocess.Popen(f'explorer "{mappe}"')
    elif sys.platform == "darwin":
        subprocess.Popen(["open", mappe])
    else:
        subprocess.Popen(["xdg-open", mappe])


def avslutt_program():  # avslutter programmet helt og stopper koden i å kjøre.
    logger.info("Program avsluttet.")
    root.destroy()
    sys.exit()



ctk.set_appearance_mode("dark")  # farge på GUI.
ctk.set_default_color_theme("blue")  # farge på knapper.

root = ctk.CTk()
root.title("Elevfordeling")
root.attributes("-fullscreen", True)  # Gjør at programmet åpnes i kantløs fullskjerm
root.bind("<Escape>", lambda e: avslutt_program())  # gjør at programmet kan avsluttes ved å trykke ESC på tastaturet
root.protocol("WM_DELETE_WINDOW", avslutt_program)

data = les_data()



"""
Boks/figur som inneholder avslutt program-knappen og programmets tittel
"""
topbar = ctk.CTkFrame(root)
topbar.pack(fill="x")

topbar.grid_columnconfigure(0, weight=0)
topbar.grid_columnconfigure(1, weight=1)
topbar.grid_columnconfigure(2, weight=0)

title_label = ctk.CTkLabel(
    topbar,
    text="Elevstatistikk, VG2 Informasjonsteknologi – Kongsberg vgs",
    font=("Arial", 36),
)
title_label.grid(row=0, column=0, padx=55, pady=20)

ctk.CTkButton(
    topbar,
    text="Avslutt program",
    fg_color="red",
    hover_color="#8B0000",
    command=avslutt_program,
).grid(row=0, column=2, padx=50, sticky="e")



"""
Grensesnitt og layout
"""
main_frame = ctk.CTkFrame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

main_frame.grid_columnconfigure(0, weight=0)
main_frame.grid_columnconfigure(1, weight=1)
main_frame.grid_rowconfigure(0, weight=1)



"""
Venstre panel med input-bokser og knapper for plotting av data
"""
input_panel = ctk.CTkFrame(main_frame)
input_panel.grid(row=0, column=0, sticky="n", padx=40, pady=40)

input_content = ctk.CTkFrame(input_panel, fg_color="transparent")
input_content.grid(row=0, column=0, sticky="nw", padx=10, pady=5)

ctk.CTkLabel(input_content, text="Skoleår:").grid(row=0, column=0, sticky="w")
entry_aar = ctk.CTkEntry(input_content, width=220)
entry_aar.grid(row=1, column=0, sticky="w", pady=(0, 8))

ctk.CTkLabel(input_content, text="Elever totalt:").grid(row=2, column=0, sticky="w")
entry_elever = ctk.CTkEntry(input_content, width=220)
entry_elever.grid(row=3, column=0, sticky="w", pady=(0, 8))

ctk.CTkLabel(input_content, text="Lærlinger:").grid(row=4, column=0, sticky="w")
entry_laerlinger = ctk.CTkEntry(input_content, width=220)
entry_laerlinger.grid(row=5, column=0, sticky="w", pady=(0, 8))

ctk.CTkLabel(input_content, text="Påbygg:").grid(row=6, column=0, sticky="w")
entry_pabygg = ctk.CTkEntry(input_content, width=220)
entry_pabygg.grid(row=7, column=0, sticky="w", pady=(0, 8))

ctk.CTkLabel(input_content, text="Annet:").grid(row=8, column=0, sticky="w")
entry_annet = ctk.CTkEntry(input_content, width=220)
entry_annet.grid(row=9, column=0, sticky="w", pady=(0, 12))

ctk.CTkButton(
    input_content, text="Legg til / endre", command=legg_til_eller_endre
).grid(row=10, column=0, sticky="w", pady=(0, 6))

ctk.CTkButton(input_content, text="Slett", command=slett_data).grid(
    row=11, column=0, sticky="w", pady=(0, 12)
)

label_path = ctk.CTkLabel(
    input_content, text=f"Lagringsplass: {os.path.abspath(DATA_FILE)}"
)
label_path.grid(row=12, column=0, sticky="w", pady=(0, 6))

ctk.CTkButton(
    input_content, text="Endre lagringsplass", command=velg_lagringsplass
).grid(row=13, column=0, sticky="w")

ctk.CTkButton(input_content, text="Åpne mappe", command=åpne_mappe).grid(
    row=14, column=0, sticky="w"
)



"""
Panel for å vise sektordiagrammet til høyre for panelet.
"""
graph_frame = ctk.CTkFrame(main_frame)
graph_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)

aarsknapper_frame = ctk.CTkFrame(graph_frame)
aarsknapper_frame.pack(pady=10)

graf_container = ctk.CTkFrame(graph_frame)
graf_container.pack(fill="both", expand=True)

oppdater_aarsknapper()
root.mainloop()