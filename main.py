import argparse
import itertools
from zxcvbn import zxcvbn
import nltk
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Download NLTK data if not already present ---
try:
    nltk.data.find('corpora/words')
except LookupError:
    print("NLTK 'words' corpus not found. Downloading now...")
    nltk.download('words')
    print("Download complete.\n")

# --- Helper Functions for Wordlist Generation ---

def apply_leetspeak(word):
    """Applies common leetspeak transformations to a word."""
    leet_map = {
        'a': ['4', '@'], 'e': ['3'], 'i': ['1', '!'], 'o': ['0'],
        's': ['5', '$'], 't': ['7', '+'], 'l': ['1', '|'], 'g': ['9'],
        'z': ['2'], 'b': ['8'], 'v': ['\\/']
    }
    transformed_words = {word}
    for char, subs in leet_map.items():
        if char in word.lower():
            for sub in subs:
                transformed_words.add(word.lower().replace(char, sub))
                transformed_words.add(word.lower().replace(char, sub).capitalize())
                transformed_words.add(word.lower().replace(char, sub).upper())
    return list(transformed_words)


def apply_common_suffixes_prefixes(word):
    """Appends common suffixes and prefixes."""
    modified_words = {word}
    common_suffixes = ["1", "123", "!", "@", "#", "$", "!!", "?", "0", "01", "21", "23", "99"]
    common_prefixes = ["!", "@", "#", "$", "pass", "admin", "user", "login"]
    for suffix in common_suffixes:
        modified_words.add(word + suffix)
        modified_words.add(word.capitalize() + suffix)
        modified_words.add(word.upper() + suffix)
    for prefix in common_prefixes:
        modified_words.add(prefix + word)
        modified_words.add(prefix + word.capitalize())
        modified_words.add(prefix + word.upper())
    return list(modified_words)

# --- Core Functions ---

def analyze_password_strength(password):
    """Analyzes the strength of a given password using zxcvbn."""
    if not password:
        return "Please enter a password to analyze."

    result = zxcvbn(password)
    output = []
    output.append(f"--- Analyzing Password: '{password}' ---\n")
    output.append(f"Strength Score (0-4): {result['score']}")
    output.append(f"Estimated Guesses: {result['guesses']}")
    output.append(f"Crack Time (online 100/hr): {result['crack_times_display']['online_throttling_100_per_hour']}")
    output.append(f"Crack Time (offline fast): {result['crack_times_display']['offline_fast_hashing_1e10_per_second']}")

    if result['feedback']['warning']:
        output.append(f"\nWarning: {result['feedback']['warning']}")
    if result['feedback']['suggestions']:
        output.append("\nSuggestions:")
        for s in result['feedback']['suggestions']:
            output.append(f"- {s}")

    return "\n".join(output)


def generate_custom_wordlist(name="", dob="", pet_name="", favorite_color="", append_years=True, output_file="custom_wordlist.txt"):
    """Generates a custom password wordlist."""
    base_words = set()
    inputs = [name, dob, pet_name, favorite_color]
    for val in inputs:
        if val:
            base_words.update({val, val.lower(), val.capitalize(), val.upper()})

    dob_warnings = []
    if dob:
        try:
            date_obj = datetime.strptime(dob, '%Y-%m-%d')
            patterns = ['%Y', '%y', '%m', '%d', '%m%d', '%d%m', '%Y%m%d', '%m%d%Y', '%d%m%Y']
            for p in patterns:
                base_words.add(date_obj.strftime(p))
        except ValueError:
            dob_warnings.append(f"⚠️ Invalid DOB '{dob}' (expected YYYY-MM-DD). Using raw input.")
            base_words.add(dob)

    # Add common weak words
    base_words.update(["password", "admin", "qwerty", "welcome", "test", "root", "secret", "user", "secure", "123456"])

    generated_words = set(base_words)
    for word in list(generated_words):
        generated_words.update(apply_leetspeak(word))
        generated_words.update(apply_common_suffixes_prefixes(word))

    if append_years:
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 20, current_year + 1)]
        for word in list(generated_words):
            for year in years:
                generated_words.add(word + year)
                generated_words.add(year + word)
                if len(year) == 4:
                    generated_words.add(word + year[2:])

    final_wordlist = sorted(list(generated_words))
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for word in final_wordlist:
            f.write(word + "\n")

    output = [f"✅ Generated {len(final_wordlist)} words.", f"📁 Saved to: {output_file}"]
    if dob_warnings:
        output.extend(dob_warnings)
    return "\n".join(output)

# --- Tkinter GUI ---

class PasswordToolGUI:
    def __init__(self, master):
        self.master = master
        master.title("Password Analyzer & Wordlist Generator")
        master.geometry("800x700")
        master.configure(bg="#2C3E50")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#34495E")
        style.configure("TLabel", background="#34495E", foreground="#ECF0F1")
        style.configure("TButton", background="#E74C3C", foreground="#ECF0F1")

        notebook = ttk.Notebook(master)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.analyzer_tab = ttk.Frame(notebook)
        self.generator_tab = ttk.Frame(notebook)
        notebook.add(self.analyzer_tab, text="Password Analyzer")
        notebook.add(self.generator_tab, text="Wordlist Generator")

        self.create_analyzer_tab()
        self.create_generator_tab()

    def create_analyzer_tab(self):
        frame = ttk.LabelFrame(self.analyzer_tab, text="Password Strength", padding=10)
        frame.pack(fill="x", pady=10)

        ttk.Label(frame, text="Password:").grid(row=0, column=0, sticky="w")
        self.password_entry = ttk.Entry(frame, show="*", width=40)
        self.password_entry.grid(row=0, column=1, padx=5)

        self.show_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Show", variable=self.show_var, command=self.toggle_password).grid(row=0, column=2)

        ttk.Button(frame, text="Analyze", command=self.run_analyze).grid(row=1, column=0, columnspan=3, pady=10)

        self.output_text = tk.Text(self.analyzer_tab, height=15, bg="#2C3E50", fg="#ECF0F1", wrap="word")
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_password(self):
        self.password_entry.config(show="" if self.show_var.get() else "*")

    def run_analyze(self):
        pwd = self.password_entry.get()
        self.output_text.delete(1.0, tk.END)
        result = analyze_password_strength(pwd)
        self.output_text.insert(tk.END, result)

    def create_generator_tab(self):
        frame = ttk.LabelFrame(self.generator_tab, text="Inputs", padding=10)
        frame.pack(fill="x", pady=10)

        labels = ["Name", "Date of Birth (YYYY-MM-DD)", "Pet Name", "Favorite Color"]
        self.inputs = {}
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.inputs[label.split()[0].lower()] = entry

        ttk.Label(frame, text="Output File:").grid(row=4, column=0, sticky="w", pady=2)
        self.output_file_entry = ttk.Entry(frame, width=40)
        self.output_file_entry.insert(0, "custom_wordlist.txt")
        self.output_file_entry.grid(row=4, column=1, padx=5, pady=2)
        ttk.Button(frame, text="Browse", command=self.browse_output).grid(row=4, column=2, padx=5)

        self.append_years = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Append Years", variable=self.append_years).grid(row=5, column=0, sticky="w", pady=5)

        ttk.Button(frame, text="Generate Wordlist", command=self.run_generate).grid(row=6, column=0, columnspan=3, pady=10)

        self.output_box = tk.Text(self.generator_tab, height=10, bg="#2C3E50", fg="#ECF0F1", wrap="word")
        self.output_box.pack(fill="both", expand=True, padx=10, pady=10)

    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            self.output_file_entry.delete(0, tk.END)
            self.output_file_entry.insert(0, path)

    def run_generate(self):
        name = self.inputs["name"].get()
        dob = self.inputs["date"].get()
        pet = self.inputs["pet"].get()
        color = self.inputs["favorite"].get()
        file = self.output_file_entry.get()
        append = self.append_years.get()

        self.output_box.delete(1.0, tk.END)
        if not any([name, dob, pet, color]):
            self.output_box.insert(tk.END, "Please enter at least one input field.")
            return

        try:
            msg = generate_custom_wordlist(name, dob, pet, color, append, file)
            self.output_box.insert(tk.END, msg)
            messagebox.showinfo("Success", "Wordlist generated successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.output_box.insert(tk.END, f"Error: {e}")

# --- CLI / Main Launcher ---

def main():
    parser = argparse.ArgumentParser(description="Password Strength Analyzer & Wordlist Generator")
    sub = parser.add_subparsers(dest="cmd")

    analyze = sub.add_parser("analyze", help="Analyze password strength")
    analyze.add_argument("password", type=str)

    gen = sub.add_parser("generate", help="Generate a wordlist")
    gen.add_argument("-n", "--name", default="")
    gen.add_argument("-d", "--dob", default="")
    gen.add_argument("-p", "--pet", default="")
    gen.add_argument("-c", "--color", default="")
    gen.add_argument("-o", "--output", default="custom_wordlist.txt")
    gen.add_argument("--no-years", action="store_true")

    args = parser.parse_args()

    if args.cmd is None:
        print("Launching GUI... (use --help for CLI options)")
        root = tk.Tk()
        PasswordToolGUI(root)
        root.mainloop()
    elif args.cmd == "analyze":
        print(analyze_password_strength(args.password))
    elif args.cmd == "generate":
        print(generate_custom_wordlist(
            name=args.name,
            dob=args.dob,
            pet_name=args.pet,
            favorite_color=args.color,
            append_years=not args.no_years,
            output_file=args.output
        ))

if __name__ == "__main__":
    main()




