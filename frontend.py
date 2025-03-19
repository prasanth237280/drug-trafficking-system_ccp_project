import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from pymongo import MongoClient

# MongoDB Setup
mongo_client = MongoClient("mongodb+srv://Prasanth2310:Yogarajvijayabanu7280@project1.15nmf.mongodb.net/?retryWrites=true&w=majority&appName=Project1")
db = mongo_client["drug_detection"]
collection = db["channel_mentions"]

# Fetch All Users from MongoDB
def get_all_users():
    return list(collection.find())

# Refresh Data
def refresh_data():
    for row in tree.get_children():
        tree.delete(row)

    all_users = get_all_users()

    total_label.config(text=f"Total Accounts: {len(all_users)}")

    for user in all_users:
        tree.insert("", "end", values=(user.get("username"), user.get("message"), user.get("risk_score"), user.get("channel"), user.get("date")))

    if not all_users:
        messagebox.showinfo("Info", "No accounts found.")

# GUI Setup
root = tk.Tk()
root.title("🚨 RISK SCORE CALCULATION")
root.geometry("1000x600")

# Total Accounts Label
total_label = tk.Label(root, text="Total Accounts: 0", font=("Arial", 14))
total_label.pack(pady=10)

# Table (Treeview)
columns = ("Username", "Message", "Risk Score", "Channel", "Date")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(expand=True, fill="both", padx=10, pady=10)

# Refresh Button
refresh_button = tk.Button(root, text="Refresh", command=refresh_data)
refresh_button.pack(pady=10)

# Initial Data Load
refresh_data()

# Run the Application
root.mainloop()
