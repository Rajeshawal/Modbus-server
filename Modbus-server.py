import tkinter as tk
from tkinter import ttk
import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import threading
import sys

# Initial data blocks
holding_data = [0] * 100
coil_data = [False] * 20           # Limit coils to 20
discrete_data = [False] * 100
input_data = [0] * 100

store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, holding_data),
    co=ModbusSequentialDataBlock(0, coil_data),
    di=ModbusSequentialDataBlock(0, discrete_data),
    ir=ModbusSequentialDataBlock(0, input_data),
)
context = ModbusServerContext(slaves=store, single=True)

# Modbus identity (unchanged)
identity = ModbusDeviceIdentification()
identity.VendorName = "ModbusPalGUI"
identity.ProductCode = "MPG"
identity.VendorUrl = "http://localhost"
identity.ProductName = "ModbusPal Inspired Server"
identity.ModelName = "ModbusPalGUI"
identity.MajorMinorRevision = "1.0"

class ModbusServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ModbusPal Inspired GUI Server")
        self.server_running = False

        # --- Port and Status Controls ---
        tk.Label(root, text="Port:").pack()
        self.port_entry = tk.Entry(root); self.port_entry.insert(0, "5020"); self.port_entry.pack()
        self.status_label = tk.Label(root, text="Status: Stopped", fg="red"); self.status_label.pack()
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server); self.start_button.pack()
        self.stop_button  = tk.Button(root, text="Stop Server",  command=self.stop_server, state=tk.DISABLED); self.stop_button.pack()

        # --- Notebook for each data type ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Holding Registers Tab
        self.holding_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.holding_frame, text="Holding Registers")
        self.holding_table = ttk.Treeview(self.holding_frame, columns=("Address","Value"), show="headings", selectmode="browse")
        self.holding_table.heading("Address", text="Address"); self.holding_table.heading("Value", text="Value")
        self.holding_table.pack(side=tk.LEFT, fill="both", expand=True)
        holding_scroll = ttk.Scrollbar(self.holding_frame, orient="vertical", command=self.holding_table.yview)
        holding_scroll.pack(side=tk.RIGHT, fill="y")
        self.holding_table.configure(yscrollcommand=holding_scroll.set)
        self.holding_table.bind("<Double-1>", self.on_double_click_holding)

        # Coils Tab
        self.coils_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.coils_frame, text="Coils")
        self.coil_table = ttk.Treeview(self.coils_frame, columns=("Address","Value"), show="headings", selectmode="browse")
        self.coil_table.heading("Address", text="Address"); self.coil_table.heading("Value", text="Value")
        self.coil_table.pack(side=tk.LEFT, fill="both", expand=True)
        coil_scroll = ttk.Scrollbar(self.coils_frame, orient="vertical", command=self.coil_table.yview)
        coil_scroll.pack(side=tk.RIGHT, fill="y")
        self.coil_table.configure(yscrollcommand=coil_scroll.set)
        self.coil_table.bind("<Double-1>", self.on_double_click_coil)

        # Discrete Inputs Tab
        self.discrete_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.discrete_frame, text="Discrete Inputs")
        self.discrete_table = ttk.Treeview(self.discrete_frame, columns=("Address","Value"), show="headings", selectmode="browse")
        self.discrete_table.heading("Address", text="Address"); self.discrete_table.heading("Value", text="Value")
        self.discrete_table.pack(side=tk.LEFT, fill="both", expand=True)
        discrete_scroll = ttk.Scrollbar(self.discrete_frame, orient="vertical", command=self.discrete_table.yview)
        discrete_scroll.pack(side=tk.RIGHT, fill="y")
        self.discrete_table.configure(yscrollcommand=discrete_scroll.set)
        self.discrete_table.bind("<Double-1>", self.on_double_click_discrete)

        # Input Registers Tab
        self.input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="Input Registers")
        self.input_table = ttk.Treeview(self.input_frame, columns=("Address","Value"), show="headings", selectmode="browse")
        self.input_table.heading("Address", text="Address"); self.input_table.heading("Value", text="Value")
        self.input_table.pack(side=tk.LEFT, fill="both", expand=True)
        input_scroll = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.input_table.yview)
        input_scroll.pack(side=tk.RIGHT, fill="y")
        self.input_table.configure(yscrollcommand=input_scroll.set)
        self.input_table.bind("<Double-1>", self.on_double_click_input)

        # Initial population and start sync loop
        self.update_holding_table(); self.update_coil_table()
        self.update_discrete_table(); self.update_input_table()
        self.root.after(1000, self.sync_data_from_store)

    def update_holding_table(self):
        self.holding_table.delete(*self.holding_table.get_children())
        for i, val in enumerate(store.getValues(3, 0, count=100)):
            self.holding_table.insert("", "end", values=(i, val))

    def update_coil_table(self):
        self.coil_table.delete(*self.coil_table.get_children())
        for i, val in enumerate(store.getValues(1, 0, count=20)):
            self.coil_table.insert("", "end", values=(i, val))

    def update_discrete_table(self):
        self.discrete_table.delete(*self.discrete_table.get_children())
        for i, val in enumerate(store.getValues(2, 0, count=100)):
            self.discrete_table.insert("", "end", values=(i, val))

    def update_input_table(self):
        self.input_table.delete(*self.input_table.get_children())
        for i, val in enumerate(store.getValues(4, 0, count=100)):
            self.input_table.insert("", "end", values=(i, val))

    def sync_data_from_store(self):
        # Refresh all tables from the store every second
        self.update_holding_table()
        self.update_coil_table()
        self.update_discrete_table()
        self.update_input_table()
        self.root.after(1000, self.sync_data_from_store)

    def on_double_click_holding(self, event):
        item = self.holding_table.selection()
        if not item: return
        item = item[0]
        address = int(self.holding_table.item(item, "values")[0])
        old_val = str(self.holding_table.item(item, "values")[1])
        x,y,width,height = self.holding_table.bbox(item, column=1)
        edit = tk.Entry(self.holding_table); edit.insert(0, old_val)
        edit.place(x=x, y=y, width=width, height=height); edit.focus()
        def save_edit(event):
            try:
                new_val = int(edit.get())
                store.setValues(3, address, [new_val])
            except ValueError:
                pass
            edit.destroy()
        edit.bind("<Return>", save_edit)
        edit.bind("<FocusOut>", lambda e: edit.destroy())

    def on_double_click_input(self, event):
        item = self.input_table.selection()
        if not item: return
        item = item[0]
        address = int(self.input_table.item(item, "values")[0])
        old_val = str(self.input_table.item(item, "values")[1])
        x,y,width,height = self.input_table.bbox(item, column=1)
        edit = tk.Entry(self.input_table); edit.insert(0, old_val)
        edit.place(x=x, y=y, width=width, height=height); edit.focus()
        def save_edit(event):
            try:
                new_val = int(edit.get())
                store.setValues(4, address, [new_val])
            except ValueError:
                pass
            edit.destroy()
        edit.bind("<Return>", save_edit)
        edit.bind("<FocusOut>", lambda e: edit.destroy())

    def on_double_click_coil(self, event):
        item = self.coil_table.selection()
        if not item: return
        item = item[0]
        address = int(self.coil_table.item(item, "values")[0])
        current_val = store.getValues(1, address, count=1)[0]
        new_val = not bool(current_val)
        store.setValues(1, address, [new_val])
        self.update_coil_table()

    def on_double_click_discrete(self, event):
        item = self.discrete_table.selection()
        if not item: return
        item = item[0]
        address = int(self.discrete_table.item(item, "values")[0])
        current_val = store.getValues(2, address, count=1)[0]
        new_val = not bool(current_val)
        store.setValues(2, address, [new_val])
        self.update_discrete_table()

    def start_server(self):
        port = int(self.port_entry.get())
        self.server_running = True
        self.status_label.config(text="Status: Running", fg="green")
        self.start_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_server, args=(port,), daemon=True).start()

    def stop_server(self):
        self.server_running = False
        self.status_label.config(text="Status: Stopped", fg="red")
        self.start_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED)
        # (Stopping the async server gracefully is non-trivial; it will close when the program exits.)

    def run_server(self, port):
        async def _run():
            await StartAsyncTcpServer(context, identity=identity, address=("0.0.0.0", port))
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(_run())

if __name__ == "__main__":
    root = tk.Tk()
    app = ModbusServerGUI(root)
    root.mainloop()