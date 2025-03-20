import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# MongoDB Setup
mongo_client = MongoClient("mongodb+srv://Prasanth2310:Yogarajvijayabanu7280@project1.15nmf.mongodb.net/?retryWrites=true&w=majority&appName=Project1")
db = mongo_client["drug_detection"]
collection = db["channel_mentions"]

# Fetch All Users from MongoDB
def get_all_users():
    return list(collection.find())

# Function to plot the Risk Score bar chart
def plot_risk_chart(data):
    # Clear previous chart
    for widget in chart_frame.winfo_children():
        widget.destroy()

    if not data:
        return

    # Extract usernames and risk scores (fill missing username with channel)
    usernames = [user.get("username") or user.get("channel", "Unknown") for user in data]
    risk_scores = [user.get("risk_score", 0) for user in data]

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    ax.bar(usernames, risk_scores, color="red")
    ax.set_title("User Risk Scores")
    ax.set_xlabel("Username")
    ax.set_ylabel("Risk Score")
    ax.set_ylim(0, 100)

    # Rotate x-axis labels to prevent overlap
    plt.xticks(rotation=45, ha="right")

    # Embed chart in Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

# Refresh Data Function
def refresh_data():
    search_term = search_entry.get().strip().lower()

    for row in tree.get_children():
        tree.delete(row)

    all_users = get_all_users()

    # Apply search filter
    if search_term:
        all_users = [
            user for user in all_users
            if search_term in str(user.get("username", "")).lower()
            or search_term in str(user.get("channel", "")).lower()
            or search_term in str(user.get("risk_score", "")).lower()
        ]

    total_label.config(text=f"Total Flagged Users: {len(all_users)}")

    for i, user in enumerate(all_users, start=1):
        # Fill username with channel if missing
        username = user.get("username") or user.get("channel", "Unknown")
        tree.insert("", "end", values=(i, username, user.get("channel"), user.get("risk_score")))

    if not all_users:
        messagebox.showinfo("Info", "No matching records found.")

    # Update chart with new data
    plot_risk_chart(all_users)

# Export Data to Excel
def export_to_excel():
    all_users = get_all_users()

    # Create DataFrame (Fill username with channel if missing)
    data = [{
        "Username": user.get("username") or user.get("channel", "Unknown"),
        "Platform": user.get("channel", ""),
        "Risk Score": user.get("risk_score", 0),
        "Date": user.get("date", "")
    } for user in all_users]

    if not data:
        messagebox.showwarning("Warning", "No data to export.")
        return

    df = pd.DataFrame(data)

    # Save to Excel
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
    if file_path:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"Data exported successfully to {file_path}")

# GUI Setup
root = tk.Tk()
root.title("Drug Trafficking Monitoring Dashboard")
root.geometry("1200x800")

# Header
header_label = tk.Label(root, text="Drug Trafficking Monitoring Dashboard", font=("Arial", 18, "bold"))
header_label.pack(pady=10)

# Total Accounts Label
total_label = tk.Label(root, text="Total Flagged Users: 0", font=("Arial", 14))
total_label.pack(pady=10)

# Search Bar
search_frame = tk.Frame(root)
search_frame.pack(pady=5)

search_label = tk.Label(search_frame, text="Search:", font=("Arial", 12))
search_label.pack(side=tk.LEFT, padx=5)

search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
search_entry.pack(side=tk.LEFT, padx=5)

search_button = tk.Button(search_frame, text="Search", command=refresh_data, font=("Arial", 12))
search_button.pack(side=tk.LEFT, padx=5)

# Table (Treeview)
columns = ("ID", "Username", "Platform", "Risk Score")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(expand=False, fill="x", padx=20, pady=10)

# Chart Frame
chart_frame = tk.Frame(root)
chart_frame.pack(padx=20, pady=20)

# Buttons (Refresh and Export)
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

refresh_button = tk.Button(button_frame, text="Refresh", command=refresh_data, font=("Arial", 12))
refresh_button.pack(side=tk.LEFT, padx=10)

export_button = tk.Button(button_frame, text="Export to Excel", command=export_to_excel, font=("Arial", 12))
export_button.pack(side=tk.LEFT, padx=10)

# Initial Data Load
refresh_data()

# Run the Application
root.mainloop()
