import requests
import time
import os
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Initialiser CustomTkinter (Mode Sombre)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  # Thème bleu

# Fonction pour récupérer l'ID utilisateur Roblox avec un proxy
def get_user_id(username, proxy=None):
    url = f"https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    
    # Si un proxy est fourni, l'ajouter à la requête
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.post(url, json=payload, proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                return data["data"][0]["id"]
    except Exception as e:
        print(f"Erreur avec le proxy {proxy}: {e}")
    return None

# Fonction pour envoyer une notification au webhook Discord
def send_to_discord(username, user_id, webhook_url, proxy=None):
    payload = {
        "content": f"✅ **Username:** {username} | **User ID:** {user_id}",
        "username": "Roblox ID Checker"
    }
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        requests.post(webhook_url, json=payload, proxies=proxies)
    except Exception as e:
        print(f"Erreur d'envoi au webhook Discord avec le proxy {proxy}: {e}")

# GUI Class
class RobloxCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox User ID Checker")
        self.root.geometry("1080x650")

        # Charger l'image de fond
        self.bg_image = Image.open("image.png")  
        self.bg_image = self.bg_image.resize((1080, 650), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        # Afficher l'image en arrière-plan
        self.bg_label = tk.Label(root, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Ajouter le texte en haut à droite
        credit_label = ctk.CTkLabel(root, text="Credit : Github @a5x", font=("Arial", 12, "italic"), text_color="white")
        credit_label.place(x=950, y=10)

        # Label du fichier
        self.file_label = ctk.CTkLabel(root, text="Put your usernames files here:", font=("Arial", 16, "bold"))
        self.file_label.pack(pady=5)

        # Frame pour organiser les boutons horizontalement
        self.buttons_frame = ctk.CTkFrame(root)
        self.buttons_frame.pack(pady=5)

        # Bouton pour sélectionner un fichier (coins carrés)
        self.file_button = ctk.CTkButton(self.buttons_frame, text="📂 Select a file", command=self.select_file, corner_radius=0)
        self.file_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour charger les proxies (coins carrés)
        self.proxy_button = ctk.CTkButton(self.buttons_frame, text="📂 Select Proxy File", command=self.select_proxy_file, corner_radius=0)
        self.proxy_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour afficher les logs (coins carrés)
        self.log_button = ctk.CTkButton(self.buttons_frame, text="📜 Show Log", command=self.show_log, corner_radius=0)
        self.log_button.pack(side=tk.LEFT, padx=5)  # Le bouton est placé à côté du bouton proxy


        # Affichage du chemin du fichier
        self.file_path = tk.StringVar()
        self.file_display = ctk.CTkLabel(root, textvariable=self.file_path, text_color="lightblue")
        self.file_display.pack()

        # Boutons Start & Stop (coins carrés)
        self.start_button = ctk.CTkButton(root, text="▶ Start Checking ids", command=self.start_checking, state=tk.DISABLED, corner_radius=0, fg_color="green", hover_color="darkgreen")
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(root, text="⛔ Stop Checking ids", command=self.stop_checking, state=tk.DISABLED, corner_radius=0, fg_color="red", hover_color="darkred")
        self.stop_button.pack(pady=5)

        # Barre de progression
        self.progress = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress.pack(pady=10)

        # Zone d'affichage des résultats
        self.output_box = ctk.CTkTextbox(root, height=300, width=600, fg_color="grey", text_color="white", corner_radius=0)
        self.output_box.pack()

        # Entrée pour le webhook Discord
        self.webhook_label = ctk.CTkLabel(root, text="Discord Webhook URL (Optional):", font=("Arial", 14))
        self.webhook_label.pack(pady=10)

        self.webhook_entry = ctk.CTkEntry(root, placeholder_text="Enter Discord Webhook URL here...", width=500)  # Modifier la largeur ici
        self.webhook_entry.pack(pady=5)

        # Option pour activer/désactiver les notifications Discord
        self.webhook_toggle_var = tk.BooleanVar(value=False)
        self.webhook_toggle = ctk.CTkSwitch(root, text="Enable Discord Notifications", command=self.toggle_webhook, variable=self.webhook_toggle_var)
        self.webhook_toggle.pack(pady=10)

        # Flag pour l'arrêt sécurisé
        self.safe_exit = False

        # Liste pour garder les résultats de l'ID utilisateur
        self.recent_checks = []

        # Liste des proxies
        self.proxies = []

    def select_proxy_file(self):
        # Boîte de dialogue pour sélectionner un fichier de proxy
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filename:
            self.load_proxies(filename)

    def load_proxies(self, filepath):
        # Charger les proxies depuis le fichier sélectionné
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                self.proxies = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Proxies loaded: {len(self.proxies)} proxies found.")
        else:
            messagebox.showerror("Erreur", "Proxy file not found!")

    def get_next_proxy(self):
        # Retourner un proxy cyclique
        if not self.proxies:
            return None
        return self.proxies.pop(0)  # Prendre le premier proxy et le retirer de la liste

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filename:
            self.file_path.set(filename)
            self.start_button.configure(state=tk.NORMAL)

    def check_user_id(self, username, proxy=None):
        user_id = get_user_id(username, proxy)
        if user_id:
            self.output_box.insert(tk.END, f"✅ {username}: {user_id}\n")
            self.output_box.yview(tk.END)  # Défilement automatique
            self.add_to_log(username, user_id)
            
            # Envoi du webhook si activé
            if self.webhook_toggle_var.get():
                webhook_url = self.webhook_entry.get()
                if webhook_url:
                    send_to_discord(username, user_id, webhook_url, proxy)
            
            return user_id
        else:
            self.output_box.insert(tk.END, f"❌ {username}: ID not found\n")
            self.output_box.yview(tk.END)  # Défilement automatique
        return None

    def start_checking(self):
        file = self.file_path.get()
        if not os.path.exists(file):
            messagebox.showerror("Erreur", "File not found!")
            return

        with open(file, "r", encoding="utf-8") as f:
            usernames = f.read().splitlines()

        if not usernames:
            messagebox.showerror("Erreur", "No usernames in the file!")
            return

        self.output_box.delete("1.0", tk.END)
        self.progress["maximum"] = len(usernames)
        self.progress["value"] = 0
        self.safe_exit = False

        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)

        output_file = "roblox_user_ids.txt"
        ids_found = []

        def run_check():
            proxy_index = 0  # Indice pour le proxy cyclique
            for username in usernames:
                if self.safe_exit:
                    break  
                
                proxy = self.proxies[proxy_index] if self.proxies else None
                result = self.check_user_id(username, proxy)
                if result:
                    ids_found.append(f"{username}: {result}")
                
                proxy_index = (proxy_index + 1) % len(self.proxies) if self.proxies else 0  # Passer au prochain proxy
                self.progress["value"] += 1
                self.root.update_idletasks()
                time.sleep(1)  # Pause de 1 seconde entre chaque requête

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(ids_found) + "\n")

            messagebox.showinfo("Done", f"Finished! User IDs saved to '{output_file}'")
            self.start_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)

        threading.Thread(target=run_check).start()

    def stop_checking(self):
        self.safe_exit = True
        self.output_box.insert(tk.END, "🛑 Stopping process...\n")
        self.output_box.yview(tk.END)  # Défilement automatique
        self.stop_button.configure(state=tk.DISABLED)

    def toggle_webhook(self):
        # Permet de contrôler l'activation des notifications Discord
        if self.webhook_toggle_var.get():
            print("Discord notifications enabled.")
        else:
            print("Discord notifications disabled.")

    def add_to_log(self, username, user_id):
        # Ajouter un nom et un ID aux logs, en limitant à 150 derniers éléments
        self.recent_checks.append(f"{username}: {user_id}")
        if len(self.recent_checks) > 150:
            self.recent_checks.pop(0)

    def show_log(self):
        # Créer une fenêtre de logs
        log_window = tk.Toplevel(self.root)
        log_window.title("Log of Last 150 Checks")
        log_window.geometry("500x400")

        # Créer une frame avec un canvas et une scrollbar
        log_frame = tk.Frame(log_window)
        log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        log_canvas = tk.Canvas(log_frame)
        log_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        log_canvas.configure(yscrollcommand=scrollbar.set)

        # Créer un widget Text pour afficher les logs
        log_text_frame = tk.Frame(log_canvas)
        log_text_frame.pack(fill=tk.BOTH, expand=True)

        log_text = tk.Text(log_text_frame, wrap=tk.WORD, height=15, width=50)
        log_text.pack(pady=10)

        # Afficher les derniers 150 noms et ID
        log_text.insert(tk.END, "\n".join(self.recent_checks))
        log_text.config(state=tk.DISABLED)

        log_canvas.create_window((0, 0), window=log_text_frame, anchor="nw")

        log_text_frame.update_idletasks()
        log_canvas.config(scrollregion=log_canvas.bbox("all"))

# Run GUI
root = ctk.CTk()
app = RobloxCheckerApp(root)
root.mainloop()
