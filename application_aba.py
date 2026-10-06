"""Interface de bureau : python3 application_aba.py."""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from ABA_generator import ABA_generator


def describe_framework(framework):
    lines = [
        f"L: [{', '.join(sorted(framework.getLiterals()))}]",
        f"A: [{', '.join(sorted(framework.getAssumptions()))}]",
        "",
        "Contraires",
    ]
    for assumption, contrary in sorted(framework.getContraries().items()):
        lines.append(f'C({assumption}): {contrary}')
    lines.extend(['', 'Regles'])
    for rule in framework.getRules():
        lines.append(f"[{rule.name}]: {rule.head} <- {', '.join(rule.body)}")
    lines.extend(['', 'Preferences'])
    preferences = sorted(framework.getPreferences())
    lines.extend(f'{stronger} > {weaker}' for stronger, weaker in preferences)
    if not preferences:
        lines.append('Aucune')
    return '\n'.join(lines)


def describe_arguments(arguments):
    lines = [f'Arguments : {len(arguments)}', '']
    for index, argument in enumerate(arguments, 1):
        support = ', '.join(sorted(argument.support))
        lines.append(f'arg_{index}: {{{support}}} |- {argument.conclusion}')
    return '\n'.join(lines)


def describe_attacks(attacks):
    lines = [f'Attaques : {len(attacks)}', '']
    for attack in attacks:
        kind = 'normale' if attack.kind == 'normal' else 'inversee'
        lines.append(
            f'arg_{attack.attacker + 1} -> arg_{attack.target + 1}'
            f' | {kind} | hypothese : {attack.assumption}'
        )
    return '\n'.join(lines)


class ABAApplication:
    def __init__(self, root):
        self.root = root
        self.framework = None
        self.file_path = None
        self.busy = False
        self.results = queue.Queue()

        root.title('Framework ABA')
        root.geometry('1000x680')
        root.minsize(700, 450)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        container = ttk.Frame(root, padding=16)
        container.grid(sticky='nsew')
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)
        ttk.Label(container, text='Framework ABA', font=('TkDefaultFont', 18)).grid(
            row=0, column=0, sticky='w', pady=(0, 12),
        )

        toolbar = ttk.Frame(container)
        toolbar.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.select_button = ttk.Button(
            toolbar, text='Selectionner un fichier', command=self.select_file,
        )
        self.generate_button = ttk.Button(
            toolbar, text='Generer le framework ABA', command=self.generate,
        )
        self.details_button = ttk.Button(
            toolbar, text='Afficher les caracteristiques', command=self.show_details,
        )
        self.convert_button = ttk.Button(
            toolbar, text='Convertir : non circulaire et atomique', command=self.convert,
        )
        self.buttons = [self.select_button, self.generate_button,
                        self.details_button, self.convert_button]
        for index, button in enumerate(self.buttons):
            button.grid(row=index // 2, column=index % 2, sticky='ew', padx=4, pady=4)
        toolbar.columnconfigure((0, 1), weight=1)

        self.file_label = ttk.Label(container, text='Aucun fichier selectionne')
        self.file_label.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        container.bind('<Configure>', lambda event: self.file_label.configure(
            wraplength=max(100, event.width - 32),
        ))

        self.tabs = ttk.Notebook(container)
        self.tabs.grid(row=3, column=0, sticky='nsew')
        self.views = {}
        for title in ('Caracteristiques', 'Arguments', 'Attaques', 'Conversion'):
            view = ScrolledText(
                self.tabs, wrap=tk.WORD, font=('TkFixedFont', 11),
                padx=12, pady=12, state=tk.DISABLED,
            )
            self.tabs.add(view, text=title)
            self.views[title] = view

        self.status = tk.StringVar(value='Aucun framework charge')
        ttk.Label(container, textvariable=self.status).grid(
            row=4, column=0, sticky='w', pady=(10, 0),
        )
        self.update_buttons()

    def update_buttons(self):
        self.select_button.configure(state='disabled' if self.busy else 'normal')
        self.generate_button.configure(
            state='normal' if self.file_path and not self.busy else 'disabled',
        )
        for button in (self.details_button, self.convert_button):
            button.configure(
                state='normal' if self.framework is not None and not self.busy
                else 'disabled',
            )

    def write_view(self, title, content):
        view = self.views[title]
        view.configure(state=tk.NORMAL)
        view.delete('1.0', tk.END)
        view.insert('1.0', content)
        view.configure(state=tk.DISABLED)

    def select_file(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title='Selectionner un framework ABA',
            filetypes=[('Fichiers texte', '*.txt'), ('Tous les fichiers', '*')],
        )
        if not filename:
            return
        self.file_path = Path(filename)
        self.file_label.configure(text=str(self.file_path))
        self.framework = None
        for title in self.views:
            self.write_view(title, '')
        self.status.set('Fichier selectionne')
        self.update_buttons()

    def run_calculation(self, calculation, on_success, status):
        self.busy = True
        self.status.set(status)
        self.update_buttons()

        def worker():
            try:
                self.results.put((True, calculation()))
            except Exception as error:
                self.results.put((False, str(error)))

        def receive_result():
            try:
                success, result = self.results.get_nowait()
            except queue.Empty:
                self.root.after(50, receive_result)
                return
            self.busy = False
            if success:
                on_success(result)
            else:
                self.status.set('Echec du calcul')
                messagebox.showerror('Erreur ABA', result, parent=self.root)
            self.update_buttons()

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(50, receive_result)

    def generate(self):
        if self.file_path is None or self.busy:
            return
        file_path = self.file_path

        def calculation():
            framework = ABA_generator.from_text(file_path.read_text(encoding='utf-8'))
            return framework, framework.createArguments(), framework.createAttacks()

        def display(result):
            self.framework, arguments, attacks = result
            self.write_view('Caracteristiques', describe_framework(self.framework))
            self.write_view('Arguments', describe_arguments(arguments))
            self.write_view('Attaques', describe_attacks(attacks))
            self.write_view('Conversion', '')
            self.tabs.select(self.views['Arguments'])
            self.status.set(f'Framework genere : {len(arguments)} arguments, '
                            f'{len(attacks)} attaques')

        self.run_calculation(calculation, display, 'Generation en cours...')

    def show_details(self):
        if self.framework is not None and not self.busy:
            self.write_view('Caracteristiques', describe_framework(self.framework))
            self.tabs.select(self.views['Caracteristiques'])

    def convert(self):
        if self.framework is None or self.busy:
            return
        framework = self.framework

        def calculation():
            converted = framework.toNonCircular()
            arguments = converted.createArguments()
            attacks = converted.createAttacks()
            return '\n\n'.join([
                'Framework non circulaire et atomique',
                describe_framework(converted),
                describe_arguments(arguments), describe_attacks(attacks),
            ])

        def display(content):
            self.write_view('Conversion', content)
            self.tabs.select(self.views['Conversion'])
            self.status.set('Conversion terminee')

        self.run_calculation(calculation, display, 'Conversion en cours...')


if __name__ == '__main__':
    window = tk.Tk()
    ABAApplication(window)
    window.mainloop()