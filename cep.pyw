import tkinter as tk
from tkinter import ttk
import requests
import webbrowser

def abrir_google_maps(event):
    cep = cep_entry.get()
    r = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    dados = r.json()
    endereco = f"{dados.get('logradouro', '')}, {dados.get('bairro', '')}, {dados.get('localidade', '')}, {dados.get('uf', '')}"

    if endereco:
        url = f"https://www.google.com/maps/search/{endereco}"
        webbrowser.open(url)

def buscar_cep(event=None):
    cep = cep_entry.get()
    r = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    dados = r.json()

    resultado_text.config(text=f'CEP: {dados["cep"]}\n'
                                f'Endereço: {dados["logradouro"]}\n'
                                f'Bairro: {dados["bairro"]}\n'
                                f'Cidade: {dados["localidade"]} - {dados["uf"]}', justify=tk.LEFT, anchor="w")
    google_maps_label.config(text="Ver no Google Maps", cursor="hand2")
    google_maps_label.bind("<Button-1>", abrir_google_maps)

root = tk.Tk()
root.title("Consulta de CEP")

root.configure(bg="#f0f0f0")

style = ttk.Style()
style.configure('TLabel', font=('Arial', 16), foreground='#333')
style.configure('TEntry', font=('Arial', 16), fieldbackground='#fff')
style.configure('TLabel.TButton', font=('Arial', 16), background='#0077cc', foreground='#fff')

frame = ttk.Frame(root, padding=20)
frame.grid(row=0, column=0)

cep_label = ttk.Label(frame, text="Informe o CEP:")
cep_label.grid(row=0, column=0, sticky="w")

cep_entry = ttk.Entry(frame)
cep_entry.grid(row=0, column=1, columnspan=2, sticky="ew")
cep_entry.bind("<Return>", buscar_cep)

resultado_text = ttk.Label(frame, text="", justify=tk.LEFT, anchor="w", font=('Arial', 16))
resultado_text.grid(row=1, column=0, columnspan=4, pady=10)

google_maps_label = ttk.Label(frame, text="", font=('Arial', 16), cursor="arrow", foreground="#0077cc")
google_maps_label.grid(row=2, column=0, columnspan=4)

root.mainloop()
