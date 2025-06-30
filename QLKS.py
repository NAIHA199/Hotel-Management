import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re
import json
import os

class ManagementApp:  
    def __init__(self, root):
        self.root = root

        self.root.geometry("1500x900")
        self.root.resizable(False, False)
        self.current_window = None
        self.create_header()
        self.frames = {}

    def create_header(self):
        self.header_frame = tk.Frame(self.root, bg="blue", height=40)
        self.header_frame.pack(fill=tk.X)

        header_buttons_frame = tk.Frame(self.header_frame, bg="blue")
        header_buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        buttons = ["Quản lý phòng", "Quản lý khách hàng", "Quản lý nhân sự",
                   "Quản lý hóa đơn", "Thoát"]

        for i, btn_text in enumerate(buttons):
            btn = tk.Button(
                header_buttons_frame,
                text=btn_text,
                bg="lightblue",
                font=("Arial", 12),
                padx=20,
                pady=8,
                command=lambda t=btn_text: self.on_header_button_click(t)
            )
            if btn_text == "Thoát":
                btn.config(command=self.exit_app)

            btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        for i in range(5):
            header_buttons_frame.grid_columnconfigure(i, weight=1)

    def exit_app(self):
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát ứng dụng?")
        if confirm:
            if hasattr(self, 'current_window') and self.current_window is not None:
                if hasattr(self.current_window, 'save_data'):
                    self.current_window.save_data()
            self.root.quit()


    def save_data(self):
        """Save room data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            data_to_save = [{
                "stt": room[0],
                "floor": room[1],
                "room_number": room[2],
                "room_type": room[3],
                "price": room[4],
                "status": room[5]
            } for room in self.room_data]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {str(e)}")
    def on_header_button_click(self, button_text):
        if self.current_window is not None:
            self.current_window.destroy()

        if button_text == "Quản lý phòng":
            self.current_window = Room_Management(self.root, self)
        elif button_text == "Quản lý nhân sự":
            self.current_window = Employee_Management(self.root, self)
        elif button_text == "Quản lý khách hàng":
            self.current_window = Customer_Management(self.root)
        elif button_text == "Quản lý hóa đơn":
            self.current_window = Invoice_Management(self.root)

        if self.current_window:
            self.current_window.pack(fill="both", expand=True)


    
class Room_Management(tk.Frame):
    def __init__(self, root, main_app):
        super().__init__(root)
        self.main_app = main_app
        self.room_data = []
        self.data_file = "data/rooms.json"
        self.load_data()
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self, text="QUẢN LÝ PHÒNG", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Form frame with 2 columns
        form_frame = tk.LabelFrame(self, text="Thông Tin Phòng", padx=10, pady=10, font=("Arial", 12))
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Left column fields
        left_frame = tk.Frame(form_frame)
        left_frame.pack(side=tk.LEFT, padx=10)
        
        self.create_form_fields(left_frame, [
            ("Tầng", "floor_entry", ["1", "2", "3", "4", "5"]),
            ("Số Phòng", "room_number_entry"),
            ("Loại Phòng", "room_type_entry", ["Phòng Đơn", "Phòng Đôi", "Phòng VIP", "Phòng Gia Đình"])
        ])

        # Right column fields  
        right_frame = tk.Frame(form_frame)
        right_frame.pack(side=tk.LEFT, padx=10)
        
        self.create_form_fields(right_frame, [
            ("Giá/Ngày", "price_entry"),
            ("Trạng Thái", "status_entry", ["Trống", "Đã đặt", "Đang sử dụng"])
        ])

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("THÊM", self.add_room, "lightgreen"),
            ("SỬA", self.update_room, "lightpink"), 
            ("XÓA", self.delete_room, "lightcoral"),
            ("SƠ ĐỒ PHÒNG", self.show_room_diagram, "lightblue"),
        ]
        
        for text, command, color in buttons:
            button = tk.Button(button_frame, text=text, command=command,
                               font=("Arial", 12), bg=color, width=20)
            button.pack(side=tk.LEFT, padx=10)
            if text == "SƠ ĐỒ PHÒNG":
                self.show_map_button = button

        # Room list
        self.create_room_list()

    def create_form_fields(self, parent, fields):
        """Create form fields with labels"""
        for i, field_info in enumerate(fields):
            label_text = field_info[0]
            attr_name = field_info[1]
            values = field_info[2] if len(field_info) > 2 else None

            tk.Label(parent, text=label_text, font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=10)
        
            if values:
                widget = ttk.Combobox(parent, values=values, font=("Arial", 14), width=28, state="readonly")
            else:
                widget = tk.Entry(parent, font=("Arial", 14), width=30)
                if attr_name == "price_entry":
                    widget.bind('<KeyRelease>', self.format_price_input)
                
            widget.grid(row=i, column=1, padx=5, pady=5)
            setattr(self, attr_name, widget)

    def create_room_list(self):
        """Create room list treeview with scrollbars"""
        list_frame = tk.LabelFrame(self, text="Danh Sách Phòng", padx=10, pady=0, font=("Arial", 12))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview with scrollbars
        self.tree = ttk.Treeview(
            list_frame,
            columns=("STT", "Tầng", "Số Phòng", "Loại Phòng", "Giá/Ngày", "Trạng Thái"),
            show="headings",
            height=10
        )

        # Configure scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Configure columns
        column_widths = {
            "STT": 50, "Tầng": 80, "Số Phòng": 100,
            "Loại Phòng": 150, "Giá/Ngày": 120, "Trạng Thái": 120
        }
    
        for col, width in column_widths.items():
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=width, minwidth=width)

        # Pack everything
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
    
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select_room)
    
        # Load initial data
        self.refresh_table()

    def add_room(self):
        try:
            # Get form values
            floor = self.floor_entry.get()
            room_number = self.room_number_entry.get().strip()
            room_type = self.room_type_entry.get()
            price_str = self.price_entry.get().strip()
            status = self.status_entry.get() or "Trống"


            # Validate price specifically
            try:
                price_value = self.validate_price(price_str)
            except ValueError as e:
                raise ValueError(f"Lỗi giá phòng: {str(e)}")

            # Other validations...
            floor, room_number, room_type, _ = self.validate_room_data(
                floor, room_number, room_type, price_value
            )
            # Check for duplicate room
            if any(room[1] == floor and room[2] == room_number for room in self.room_data):
                raise ValueError("Phòng này đã tồn tại!")

            # Add new room with validated price
            new_room = (len(self.room_data) + 1, floor, room_number, 
                       room_type, price_value, status)
            self.room_data.append(new_room)
        
            self.refresh_table()
            self.save_data()
            self.clear_fields()
            messagebox.showinfo("Thành công", "Thêm phòng thành công!")
        
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))

    def refresh_table(self):
        """Refresh room list table with formatted prices"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for room in self.room_data:
            self.tree.insert('', 'end', values=(
                room[0],
                room[1],
                room[2],
                room[3],
                self.format_price_display(room[4]),  # Format price
                room[5]
            ))

    def update_room(self):
        """Update selected room"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn phòng để cập nhật!")
            return

        try:
            room_index = self.tree.index(selected[0])
            current_room = self.room_data[room_index]

            # Get updated values
            floor = self.floor_entry.get()
            room_number = self.room_number_entry.get().strip()
            room_type = self.room_type_entry.get()
            price = self.price_entry.get().strip()
            status = self.status_entry.get()

            # Validate input
            if not all([floor, room_number, room_type, price, status]):
                raise ValueError("Vui lòng nhập đầy đủ thông tin!")

            # Validate and format data
            floor, room_number, room_type, price_value = self.validate_room_data(
                floor, room_number, room_type, price
            )

            # Update room data
            updated_room = (
                current_room[0],  # Keep original STT
                floor,
                room_number,
                room_type,
                price_value,
                status
            )
            self.room_data[room_index] = updated_room
        
            self.refresh_table()
            self.save_data()
            self.clear_fields()
            messagebox.showinfo("Thành công", "Cập nhật phòng thành công!")
        
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))

    def delete_room(self):
        """Delete selected room"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn phòng để xóa!")
            return

        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa phòng này?"):
            room_index = self.tree.index(selected[0])
            self.room_data.pop(room_index)
        
            # Update STT for remaining rooms
            self.room_data = [(i+1,) + room[1:] for i, room in enumerate(self.room_data)]
        
            self.refresh_table()
            self.save_data()
            self.clear_fields()
            messagebox.showinfo("Thành công", "Xóa phòng thành công!")

    def on_select_room(self, event=None):
        """Handle room selection event"""
        selected = self.tree.selection()
        if not selected:
            return

        # Get selected room data
        item = selected[0]
        values = self.tree.item(item)['values']
    
        # Fill form fields with selected room data
        self.floor_entry.set(values[1])
        self.room_number_entry.delete(0, tk.END)
        self.room_number_entry.insert(0, values[2])
        self.room_type_entry.set(values[3])
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, values[4])
        self.status_entry.set(values[5])

    def validate_room_data(self, floor, room_number, room_type, price):
        """Validate room input data"""
        try:
            # Validate floor
            if not floor:
                raise ValueError("Vui lòng chọn tầng!")
            
            # Validate room number
            if not room_number.isdigit():
                raise ValueError("Số phòng phải là số!")
        
            room_num = int(room_number)
            if room_num < 1 or room_num > 10:
                raise ValueError("Số phòng phải từ 01-10!")
            room_number = f"{room_num:02d}"
        
            # Validate room type
            if not room_type:
                raise ValueError("Vui lòng chọn loại phòng!")
            
           # Validate price
            if isinstance(price, str):
                # Nếu price là chuỗi, xử lý chuyển đổi
                price_clean = price.replace(',', '').replace('VND', '').strip()
                try:
                    price_value = float(price_clean)
                except ValueError:
                    raise ValueError("Giá phòng không hợp lệ!")
            else:
                # Nếu price đã là số, sử dụng trực tiếp
                price_value = float(price)
        
            if price_value <= 0:
                raise ValueError("Giá phòng phải là số dương!")
            if price_value > 1000000000:  # Giới hạn giá tối đa
                raise ValueError("Giá phòng vượt quá giới hạn cho phép!")
            
            return floor, room_number, room_type, price_value

        except ValueError as e:
            raise e

    def format_price_input(self, event):
        """Format price input as currency while typing"""
        entry = event.widget
        current = entry.get()
    
        # Remove all non-digit characters except decimal point
        cleaned = ''.join(c for c in current if c.isdigit() or c == '.')
    
        try:
            # Convert to float and check validity
            if cleaned:
                value = float(cleaned)
                if value < 0:
                    raise ValueError("Giá không được âm")
                
                # Format with thousand separators and currency
                formatted = f"{value:,.0f} VND"
            
                # Update entry without triggering event again
                entry.delete(0, tk.END)
                entry.insert(0, formatted)
            
        except ValueError:
            # If invalid number, clear the field
            entry.delete(0, tk.END)

    def validate_price(self, price_str):
        """Validate and convert price string to float"""
        try:
            # Remove currency symbol and thousand separators
            cleaned = price_str.replace('VND', '').replace(',', '').strip()
        
            if not cleaned:
                return 0.0
            
            value = float(cleaned)
            if value < 0:
                raise ValueError("Giá không được âm")
            
            return value
        
        except ValueError:
            raise ValueError("Giá không hợp lệ")

    def format_price_display(self, price):
        """Format price for display"""
        try:
            return f"{float(price):,.0f} VND"
        except (ValueError, TypeError):
            return "0 VND"

    def show_room_diagram(self):
        """Display room diagram window"""
        diagram = tk.Toplevel(self)
        diagram.title("Sơ Đồ Phòng")
        diagram.geometry("1200x800")

        # Hide the show room diagram button
        self.show_map_button.pack_forget()

        # Create main container
        main_frame = tk.Frame(diagram)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add statistics bar
        stats_frame = tk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
    
        stats = self.get_room_statistics()
        stats_text = (f"Tổng số phòng: {stats['total']} | "
                     f"Phòng trống: {stats['empty']} | "
                     f"Phòng đã đặt: {stats['booked']} | "
                     f"Phòng đang sử dụng: {stats['in_use']}")
    
        tk.Label(stats_frame, text=stats_text, font=("Arial", 12)).pack()

        # Create scrollable canvas for room display
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create room grid by floor
        for floor in range(1, 6):
            floor_frame = tk.LabelFrame(scrollable_frame, text=f"Tầng {floor}", 
                                      font=("Arial", 12, "bold"))
            floor_frame.pack(fill=tk.X, pady=10)

            for row in range(2):
                for col in range(5):
                    room_num = f"{floor}{row*5 + col + 1:02d}"
                    self.create_room_card(floor_frame, room_num, row, col)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scroll region
        scrollable_frame.bind("<Configure>", 
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def process_payment(self, room_info):
        """Process room payment"""
        payment_window = tk.Toplevel(self)
        payment_window.title(f"Thanh Toán - Phòng {room_info[1]}{room_info[2]}")
        payment_window.geometry("500x600")

        # Payment information frame
        info_frame = tk.LabelFrame(payment_window, text="Thông tin thanh toán",
                                 padx=10, pady=10, font=("Arial", 12))
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Room information
        room_labels = [
            f"Số phòng: {room_info[1]}{room_info[2]}",
            f"Loại phòng: {room_info[3]}",
            f"Giá/ngày: {room_info[4]:,} VNĐ"
        ]
    
        for label in room_labels:
            tk.Label(info_frame, text=label, font=("Arial", 12)).pack(pady=5)

        # Payment details
        tk.Label(info_frame, text="Ngày nhận phòng:", font=("Arial", 12)).pack(pady=5)
        check_in_entry = tk.Entry(info_frame, font=("Arial", 12))
        check_in_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        check_in_entry.pack(pady=5)

        tk.Label(info_frame, text="Ngày trả phòng:", font=("Arial", 12)).pack(pady=5)
        check_out_entry = tk.Entry(info_frame, font=("Arial", 12))
        check_out_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        check_out_entry.pack(pady=5)

        # Calculate total amount
        def calculate_total():
            try:
                check_in = datetime.strptime(check_in_entry.get(), "%d/%m/%Y")
                check_out = datetime.strptime(check_out_entry.get(), "%d/%m/%Y")
                days = (check_out - check_in).days
                if days <= 0:
                    raise ValueError("Ngày trả phòng phải sau ngày nhận phòng!")
            
                total = days * float(str(room_info[4]).replace(',', '').replace('VND', ''))
                total_label.config(text=f"Tổng tiền: {total:,.0f} VNĐ")
                return total
            except ValueError as e:
                messagebox.showerror("Lỗi", str(e))
                return None

        # Total amount label
        total_label = tk.Label(info_frame, text="Tổng tiền: 0 VNĐ", font=("Arial", 12, "bold"))
        total_label.pack(pady=10)

        # Calculate button
        tk.Button(info_frame, text="Tính tiền",
                 command=calculate_total,
                 font=("Arial", 12), bg="lightblue", width=15).pack(pady=5)

        def confirm_payment():
            total = calculate_total()
            if total is None:
                return

            try:
                # Generate invoice ID
                invoice_id = f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create invoice data
                invoice_data = {
                    "invoice_id": invoice_id,
                    "room_number": f"{room_info[1]}{room_info[2]}",
                    "room_type": room_info[3],
                    "check_in": check_in_entry.get(),
                    "check_out": check_out_entry.get(),
                    "days": (datetime.strptime(check_out_entry.get(), "%d/%m/%Y") - 
                            datetime.strptime(check_in_entry.get(), "%d/%m/%Y")).
                    day,        
                    "price_per_day": float(str(room_info[4]).replace(',', '').replace('VND', '')),
                    "deposit": 0,  # Add deposit logic if needed
                    "total": total,
                    "payment_date": datetime.now().strftime("%d/%m/%Y"),
                    "status": "Đã thanh toán"
                }

                # Update room status
                self.update_room_status(room_info, "Trống")
            
                # Save invoice data
                self.save_invoice(invoice_data)
            
                messagebox.showinfo("Thành công", "Thanh toán thành công!")
                payment_window.destroy()
            
            except Exception as e:
                messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")

        # Payment buttons
        tk.Button(info_frame, text="Xác nhận thanh toán",
                 command=confirm_payment,
                 font=("Arial", 12), bg="lightgreen", width=20).pack(pady=5)
        tk.Button(info_frame, text="Hủy",
                 command=payment_window.destroy,
                 font=("Arial", 12), bg="lightcoral", width=20).pack(pady=5)

    def save_invoice(self, invoice_data):
        """Save invoice data to file"""
        try:
            invoice_file = "data/invoices.json"
            invoices = []
        
            if os.path.exists(invoice_file):
                with open(invoice_file, 'r', encoding='utf-8') as f:
                    invoices = json.load(f)
        
            # Add new invoice
            invoices.append(invoice_data)
        
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open(invoice_file, 'w', encoding='utf-8') as f:
                json.dump(invoices, f, ensure_ascii=False, indent=4)
            
            # Update invoice management if it exists
            if hasattr(self.main_app, 'current_window') and isinstance(self.main_app.current_window, Invoice_Management):
                self.main_app.current_window.load_data()
                self.main_app.current_window.update_invoice_list()
                self.main_app.current_window.update_date_filter()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu hóa đơn: {str(e)}")

    def create_room_card(self, parent, room_num, row, col):
        """Create individual room card for diagram"""
        room_info = self.get_room_info(room_num)

        card = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        card.grid(row=row, column=col, padx=5, pady=5)

        # Set background color based on status
        bg_color = "lightgreen"  # Default for empty rooms
        if room_info:
            if room_info[5] == "Đã đặt":
                bg_color = "yellow"
            elif room_info[5] == "Đang sử dụng":
                bg_color = "red"

        # Room information
        info_text = f"Phòng {room_num}\n"
        if room_info:
            info_text += f"{room_info[3]}\n{room_info[5]}"
        else:
            info_text += "Chưa có\nTrống"

        tk.Label(card, text=info_text, width=20, height=4,
                bg=bg_color, font=("Arial", 10)).pack(pady=2)

        # Add action button based on status
        if room_info:
            if room_info[5] == "Đang sử dụng":
                tk.Button(card, text="THANH TOÁN",
                         command=lambda: self.process_payment(room_info),
                         bg="lightblue", width=15).pack(pady=2)
            elif room_info[5] == "Trống":
                tk.Button(card, text="ĐẶT PHÒNG",
                         command=lambda: self.book_room(room_info),
                         bg="lightgreen", width=15).pack(pady=2)
    def format_payment_data(self, payment_data):
        return {
            "room_id": payment_data["room_id"],
            "check_in": payment_data["check_in"],
            "check_out": payment_data["check_out"],
            "total_amount": payment_data["total_amount"],
            "payment_date": payment_data["payment_date"]
        }

    def get_room_statistics(self):
        """Get room statistics"""
        total = len(self.room_data)
        empty = sum(1 for room in self.room_data if room[5] == "Trống")
        booked = sum(1 for room in self.room_data if room[5] == "Đã đặt")
        in_use = sum(1 for room in self.room_data if room[5] == "Đang sử dụng")
    
        return {
            "total": total,
            "empty": empty,
            "booked": booked,
            "in_use": in_use
        }
    def book_room(self, room_info):
        """Book a room"""
        booking_window = tk.Toplevel(self)
        booking_window.title(f"Đặt phòng {room_info[1]}{room_info[2]}")
        booking_window.geometry("400x600")

        # Booking information frame
        info_frame = tk.LabelFrame(booking_window, text="Thông tin đặt phòng",
                                 padx=10, pady=10, font=("Arial", 12))
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Room information
        room_labels = [
            f"Số phòng: {room_info[1]}{room_info[2]}",
            f"Loại phòng: {room_info[3]}",
            f"Giá/ngày: {room_info[4]:,} VNĐ"
        ]
    
        for label in room_labels:
            tk.Label(info_frame, text=label, font=("Arial", 12)).pack(pady=5)

        # Booking fields
        fields = [
            ("Tên khách hàng:", "customer_name"),
            ("Số điện thoại:", "phone"),
            ("Ngày nhận phòng:", "check_in")
        ]

        entries = {}
        for label_text, key in fields:
            tk.Label(info_frame, text=label_text, font=("Arial", 12)).pack(pady=5)
            entry = tk.Entry(info_frame, font=("Arial", 12))
        
            if key in ["check_in"]:
                entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
            
            entry.pack(pady=5)
            entries[key] = entry

        def confirm_booking():
            try:
                # Validate booking data
                booking_data = {
                    "room_id": f"{room_info[1]}{room_info[2]}",
                    "customer_name": entries["customer_name"].get().strip(),
                    "phone": entries["phone"].get().strip(),
                    "check_in": entries["check_in"].get().strip(),
                    "status": "active"
                }

                self.validate_booking_data(booking_data)
                self.save_booking(booking_data)

                # Update room status
                self.update_room_status(room_info, "Đang sử dụng")
            
                messagebox.showinfo("Thành công", "Đặt phòng thành công!")
                booking_window.destroy()
            
            except ValueError as e:
                messagebox.showerror("Lỗi", str(e))

        # Booking buttons
        tk.Button(info_frame, text="Xác nhận đặt phòng",
                 command=confirm_booking,
                 font=("Arial", 12), bg="lightgreen", width=20).pack(pady=5)
        tk.Button(info_frame, text="Hủy",
                 command=booking_window.destroy,
                 font=("Arial", 12), bg="lightcoral", width=20).pack(pady=5)
    def save_data(self):
        """Save room data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            data_to_save = [{
                "stt": room[0],
                "floor": room[1],
                "room_number": room[2],
                "room_type": room[3],
                "price": room[4],
                "status": room[5]
            } for room in self.room_data]
        
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {str(e)}")

    def load_data(self):
        """Load room data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.room_data = [
                        (room["stt"], room["floor"], room["room_number"],
                         room["room_type"], room["price"], room["status"])
                        for room in data
                    ]
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu: {str(e)}")

    def save_booking(self, booking_data):
        """Save booking information"""
        try:
            booking_file = "data/bookings.json"
            bookings = []
        
            if os.path.exists(booking_file):
                with open(booking_file, 'r', encoding='utf-8') as f:
                    bookings = json.load(f)
        
            # Add new booking
            bookings.append(booking_data)
        
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open(booking_file, 'w', encoding='utf-8') as f:
                json.dump(bookings, f, ensure_ascii=False, indent=4)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu đặt phòng: {str(e)}")
            raise

    def save_invoice(self, invoice_data):
        """Save invoice information"""
        try:
            invoice_file = "data/invoices.json"
            invoices = []
        
            if os.path.exists(invoice_file):
                with open(invoice_file, 'r', encoding='utf-8') as f:
                    invoices = json.load(f)
        
            # Add new invoice
            invoices.append(invoice_data)
        
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open(invoice_file, 'w', encoding='utf-8') as f:
                json.dump(invoices, f, ensure_ascii=False, indent=4)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu hóa đơn: {str(e)}")
            raise

    def update_room_status(self, room_info, new_status):
        """Update room status"""
        try:
            # Find and update room status
            for i, room in enumerate(self.room_data):
                if room[1] == room_info[1] and room[2] == room_info[2]:
                    self.room_data[i] = room[:5] + (new_status,)
                    break
                
            self.refresh_table()
            self.save_data()
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật trạng thái phòng: {str(e)}")
            raise

    def clear_fields(self):
        """Clear all input fields"""
        self.floor_entry.set('')
        self.room_number_entry.delete(0, tk.END)
        self.room_type_entry.set('')
        self.price_entry.delete(0, tk.END)
        self.status_entry.set('')

    def calculate_days(self, check_in, check_out):
        """Calculate number of days between check-in and check-out"""
        start = datetime.strptime(check_in, "%d/%m/%Y")
        end = datetime.strptime(check_out, "%d/%m/%Y")
        return (end - start).days

    def validate_booking_data(self, booking_data):
        """Validate booking input data"""
        if not all([booking_data["customer_name"], booking_data["phone"]]):
            raise ValueError("Vui lòng nhập đầy đủ thông tin khách hàng!")

        try:
            check_in = datetime.strptime(booking_data["check_in"], "%d/%m/%Y")
        
            
        except ValueError as e:
            if "strptime" in str(e):
                raise ValueError("Định dạng ngày không hợp lệ (DD/MM/YYYY)!")
            raise e

      
    def get_room_info(self, room_number):
        """Get room information by room number"""
        floor = room_number[0]
        room_num = room_number[1:]
    
        for room in self.room_data:
            if room[1] == floor and room[2] == room_num:
                return room
        return None

    def refresh_table(self):
        """Refresh room list table"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for room in self.room_data:
            self.tree.insert('', 'end', values=(
                room[0],
                room[1],
                room[2],
                room[3],
                f"{room[4]:,.0f} VND",
                room[5]
            ))
class Employee_Management(tk.Frame):
    def __init__(self, root, main_app):
        super().__init__(root)
        self.main_app = main_app
        self.employee_data = []
        self.data_file = "data/employees.json"
        self.load_data()
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self, text="QUẢN LÝ NHÂN SỰ", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Search Frame
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Tìm kiếm:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(search_frame, text="Lọc theo khu vực:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.area_filter = ttk.Combobox(search_frame, values=["Tất cả"], font=("Arial", 12))
        self.area_filter.pack(side=tk.LEFT)
        self.area_filter.set("Tất cả")

        # Form frame
        form_frame = tk.LabelFrame(self, text="Thông Tin Nhân Viên", padx=10, pady=10, font=("Arial", 12))
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Input fields
        fields_left = [
            ("Tên Nhân Viên", "employee_name_entry"),
            ("Mã Nhân Viên", "employee_id_entry"),
            ("Số Điện Thoại", "phone_entry"),
        ]

        fields_right = [
            ("Khu Vực Phụ Trách", "area_entry"),
            ("Ngày Bắt Đầu", "start_date_entry"),
            ("Lương", "salary_entry"),
        ]

        # Frames for left and right columns
        left_frame = tk.Frame(form_frame)
        left_frame.pack(side=tk.LEFT, padx=10)
        right_frame = tk.Frame(form_frame)
        right_frame.pack(side=tk.LEFT, padx=10)

        # Add input fields
        for i, (label_text, attr_name) in enumerate(fields_left):
            tk.Label(left_frame, text=label_text, font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=10)
            setattr(self, attr_name, tk.Entry(left_frame, font=("Arial", 14), width=30))
            entry = getattr(self, attr_name)
            entry.grid(row=i, column=1, padx=5, pady=5)

        for i, (label_text, attr_name) in enumerate(fields_right):
            tk.Label(right_frame, text=label_text, font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=10)
            setattr(self, attr_name, tk.Entry(right_frame, font=("Arial", 14), width=30))
            entry = getattr(self, attr_name)
            entry.grid(row=i, column=1, padx=5, pady=5)

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="THÊM", font=("Arial", 12), command=self.add_employee,
                 bg="lightgreen", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="SỬA", font=("Arial", 12), command=self.update_employee,
                 bg="lightpink", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="XÓA", font=("Arial", 12), command=self.delete_employee,
                 bg="lightcoral", width=20).pack(side=tk.LEFT, padx=10)
        

        # Employee list
        list_frame = tk.LabelFrame(self, text="Danh Sách Nhân Viên", padx=10, pady=0, font=("Arial", 12))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create Treeview with scrollbar
        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("STT", "Tên Nhân Viên", "Mã Nhân Viên", "Số Điện Thoại", "Khu Vực", "Ngày Bắt Đầu", "Lương"),
            show="headings",
            height=10,
        )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.search_entry.bind('<KeyRelease>', self.search_employees)
        self.area_filter.bind('<<ComboboxSelected>>', self.filter_employees)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Load initial data
        self.refresh_table()
    def add_employee(self):
        """Thêm nhân viên mới"""
        try:
            # Lấy thông tin từ các trường nhập liệu
            employee_info = self.get_form_data()
            
            # Validate dữ liệu
            self.validate_employee_data(employee_info)
            
            # Tạo STT mới
            stt = len(self.employee_data) + 1
            
            # Thêm vào danh sách
            employee_record = (
                stt,
                employee_info['name'],
                employee_info['id'],
                employee_info['phone'],
                employee_info['area'],
                employee_info['start_date'],
                employee_info['salary']
            )
            
            self.employee_data.append(employee_record)
            self.refresh_table()
            self.clear_form()
            self.save_data()
            
            messagebox.showinfo("Thành công", "Đã thêm nhân viên mới!")
            
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def update_employee(self):
        """Cập nhật thông tin nhân viên"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần cập nhật!")
            return

        try:
            # Lấy thông tin từ form
            employee_info = self.get_form_data()
            
            # Validate dữ liệu
            self.validate_employee_data(employee_info)
            
            # Cập nhật thông tin
            selected_item = selected_items[0]
            item_values = self.tree.item(selected_item)['values']
            stt = item_values[0]
            
            # Tìm và cập nhật trong employee_data
            for i, emp in enumerate(self.employee_data):
                if emp[0] == stt:
                    self.employee_data[i] = (
                        stt,
                        employee_info['name'],
                        employee_info['id'],
                        employee_info['phone'],
                        employee_info['area'],
                        employee_info['start_date'],
                        employee_info['salary']
                    )
                    break
            
            self.refresh_table()
            self.save_data()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin nhân viên!")
            
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def delete_employee(self):
        """Xóa nhân viên"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần xóa!")
            return

        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa nhân viên này?"):
            try:
                selected_item = selected_items[0]
                item_values = self.tree.item(selected_item)['values']
                stt = item_values[0]
                
                # Xóa khỏi employee_data
                self.employee_data = [emp for emp in self.employee_data if emp[0] != stt]
                
                # Cập nhật lại STT
                for i, emp in enumerate(self.employee_data, 1):
                    self.employee_data[i-1] = (i,) + emp[1:]
                
                self.refresh_table()
                self.clear_form()
                self.save_data()
                messagebox.showinfo("Thành công", "Đã xóa nhân viên!")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi xóa nhân viên: {str(e)}")

    def get_form_data(self):
        """Lấy dữ liệu từ form"""
        return {
            'name': self.employee_name_entry.get().strip(),
            'id': self.employee_id_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'area': self.area_entry.get().strip(),
            'start_date': self.start_date_entry.get().strip(),
            'salary': self.salary_entry.get().strip()
        }

    def validate_employee_data(self, data):
        """Kiểm tra tính hợp lệ của dữ liệu"""
        if not all(data.values()):
            raise ValueError("Vui lòng nhập đầy đủ thông tin!")
            
        if not re.match(r'^\d{10}$', data['phone']):
            raise ValueError("Số điện thoại không hợp lệ (phải có 10 chữ số)!")
            
        if not re.match(r'^\d{4,6}$', data['id']):
            raise ValueError("Mã nhân viên không hợp lệ (phải có 4-6 chữ số)!")
            
        try:
            salary = float(data['salary'])
            if salary <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("Lương phải là số dương!")
            
        # Kiểm tra định dạng ngày tháng (DD/MM/YYYY)
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', data['start_date']):
            raise ValueError("Ngày bắt đầu không hợp lệ (định dạng: DD/MM/YYYY)!")
        
    def search_employees(self, event=None):
        """Tìm kiếm nhân viên"""
        search_text = self.search_entry.get().lower()
        area_filter = self.area_filter.get()
        
        # Xóa dữ liệu cũ trong bảng
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Lọc và hiển thị kết quả
        for emp in self.employee_data:
            if (search_text in emp[1].lower() or  # Tên
                search_text in emp[2].lower() or  # Mã
                search_text in emp[3].lower()):   # Số điện thoại
                
                if area_filter == "Tất cả" or area_filter == emp[4]:
                    self.tree.insert('', 'end', values=emp)

    def filter_employees(self, event=None):
        """Lọc nhân viên theo khu vực"""
        self.search_employees()

    def on_select(self, event=None):
        """Xử lý sự kiện khi chọn một nhân viên trong bảng"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # Lấy thông tin nhân viên được chọn
        item = selected_items[0]
        values = self.tree.item(item)['values']
        
        # Điền thông tin vào form
        self.employee_name_entry.delete(0, tk.END)
        self.employee_name_entry.insert(0, values[1])
        
        self.employee_id_entry.delete(0, tk.END)
        self.employee_id_entry.insert(0, values[2])
        
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, values[3])
        
        self.area_entry.delete(0, tk.END)
        self.area_entry.insert(0, values[4])
        
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, values[5])
        
        self.salary_entry.delete(0, tk.END)
        self.salary_entry.insert(0, values[6])

    def clear_form(self):
        """Xóa tất cả dữ liệu trong form"""
        self.employee_name_entry.delete(0, tk.END)
        self.employee_id_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.area_entry.delete(0, tk.END)
        self.start_date_entry.delete(0, tk.END)
        self.salary_entry.delete(0, tk.END)

    def refresh_table(self):
        """Cập nhật lại bảng dữ liệu"""
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Thêm dữ liệu mới
        for emp in self.employee_data:
            self.tree.insert('', 'end', values=emp)
            
        # Cập nhật danh sách khu vực trong combobox
        areas = set(emp[4] for emp in self.employee_data)
        self.area_filter['values'] = ["Tất cả"] + list(areas)

    def save_data(self):
        """Lưu dữ liệu vào file"""
        try:
            os.makedirs('data', exist_ok=True)
            data_to_save = []
            for emp in self.employee_data:
                emp_dict = {
                    "stt": emp[0],
                    "name": emp[1],
                    "id": emp[2],
                    "phone": emp[3],
                    "area": emp[4],
                    "start_date": emp[5],
                    "salary": emp[6]
                }
                data_to_save.append(emp_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {str(e)}")

    def load_data(self):
        """Đọc dữ liệu từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.employee_data = [
                        (
                            emp["stt"],
                            emp["name"],
                            emp["id"],
                            emp["phone"],
                            emp["area"],
                            emp["start_date"],
                            emp["salary"]
                        )
                        for emp in data
                    ]
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu: {str(e)}")
class Customer_Management(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.customer_data = []
        self.data_file = "data/customers.json"
        self.load_data()
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self, text="QUẢN LÝ KHÁCH HÀNG", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Search Frame
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Tìm kiếm:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(search_frame, text="Lọc theo địa chỉ:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.address_filter = ttk.Combobox(search_frame, values=["Tất cả"], font=("Arial", 12))
        self.address_filter.pack(side=tk.LEFT)
        self.address_filter.set("Tất cả")

        # Form frame
        form_frame = tk.LabelFrame(self, text="Thông Tin Khách Hàng", padx=10, pady=10, font=("Arial", 12))
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Input fields
        fields = [
            ("Mã Khách Hàng", "customer_id_entry"),
            ("Tên Khách Hàng", "customer_name_entry"),
            ("Số Điện Thoại", "phone_entry"),
            ("Địa Chỉ", "address_entry"),
            ("CCCD", "id_card_entry")
        ]

        for i, (label_text, attr_name) in enumerate(fields):
            tk.Label(form_frame, text=label_text, font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=10)
            setattr(self, attr_name, tk.Entry(form_frame, font=("Arial", 14), width=30))
            entry = getattr(self, attr_name)
            entry.grid(row=i, column=1, padx=5, pady=5)

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="THÊM", font=("Arial", 12), command=self.add_customer,
                 bg="lightgreen", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="SỬA", font=("Arial", 12), command=self.update_customer,
                 bg="lightpink", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="XÓA", font=("Arial", 12), command=self.delete_customer,
                 bg="lightcoral", width=20).pack(side=tk.LEFT, padx=10)
        
        # Customer list
        list_frame = tk.LabelFrame(self, text="Danh Sách Khách Hàng", padx=10, pady=0, font=("Arial", 12))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create Treeview with scrollbar
        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("STT", "Mã KH", "Tên KH", "Số ĐT", "Địa Chỉ", "CCCD"),
            show="headings",
            height=10,
        )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.search_entry.bind('<KeyRelease>', self.search_customers)
        self.address_filter.bind('<<ComboboxSelected>>', self.filter_customers)

    def validate_input(self, customer_id, name, phone, id_card):
        if len(customer_id) < 1:
            raise ValueError("Mã khách hàng không được để trống!")
            
        if len(name) < 2:
            raise ValueError("Tên khách hàng phải có ít nhất 2 ký tự!")
            
        if not re.match(r'^(0|\+84)[0-9]{9}$', phone):
            raise ValueError("Số điện thoại không hợp lệ!")
            
        if not re.match(r'^[0-9]{12}$', id_card):
            raise ValueError("CCCD phải có 12 chữ số!")

    def add_customer(self):
        try:
            customer_id = self.customer_id_entry.get().strip()
            name = self.customer_name_entry.get().strip()
            phone = self.phone_entry.get().strip()
            address = self.address_entry.get().strip()
            id_card = self.id_card_entry.get().strip()

            if not all([customer_id, name, phone, address, id_card]):
                raise ValueError("Vui lòng nhập đầy đủ thông tin!")

            # Validate input
            self.validate_input(customer_id, name, phone, id_card)
            
            # Check for duplicate customer ID and ID card
            if any(cust[1] == customer_id for cust in self.customer_data):
                raise ValueError("Mã khách hàng đã tồn tại!")
            if any(cust[5] == id_card for cust in self.customer_data):
                raise ValueError("CCCD đã tồn tại!")

            self.customer_data.append((len(self.customer_data) + 1, customer_id, name, phone, address, id_card))
            self.update_customer_list()
            self.update_address_filter()
            self.save_data()
            self.clear_fields()
            messagebox.showinfo("Thành công", "Khách hàng đã được thêm!")
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))

    def update_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn khách hàng để chỉnh sửa!")
            return

        cust_index = self.tree.index(selected[0])
        customer = self.customer_data[cust_index]

        # Tạo cửa sổ mới cho việc chỉnh sửa
        edit_window = tk.Toplevel(self)
        edit_window.title("Chỉnh sửa thông tin khách hàng")
        edit_window.geometry("600x400")
        
        # Form frame
        form_frame = tk.LabelFrame(edit_window, text="Thông tin khách hàng", padx=10, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create and fill fields
        fields = [
            ("Mã khách hàng:", customer[1]),
            ("Tên khách hàng:", customer[2]),
            ("Số điện thoại:", customer[3]),
            ("Địa chỉ:", customer[4]),
            ("CCCD:", customer[5])
        ]
        
        entries = {}
        for i, (label_text, value) in enumerate(fields):
            tk.Label(form_frame, text=label_text, font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            entry = tk.Entry(form_frame, font=("Arial", 12), width=30)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[label_text] = entry
            
            # Disable customer ID and ID card fields
            if label_text in ["Mã khách hàng:", "CCCD:"]:
                entry.config(state='readonly')

        def save_changes():
            try:
                customer_id = entries["Mã khách hàng:"].get().strip()
                name = entries["Tên khách hàng:"].get().strip()
                phone = entries["Số điện thoại:"].get().strip()
                address = entries["Địa chỉ:"].get().strip()
                id_card = entries["CCCD:"].get().strip()

                if not all([customer_id, name, phone, address, id_card]):
                    raise ValueError("Vui lòng nhập đầy đủ thông tin!")

                self.validate_input(customer_id, name, phone, id_card)

                self.customer_data[cust_index] = (
                    cust_index + 1,
                    customer_id,
                    name,
                    phone,
                    address,
                    id_card
                )
                
                self.update_customer_list()
                self.update_address_filter()
                self.save_data()
                messagebox.showinfo("Thành công", "Đã cập nhật thông tin khách hàng!")
                edit_window.destroy()

            except ValueError as e:
                messagebox.showerror("Lỗi", str(e))

        # Button frame
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="LƯU",
            command=save_changes,
            font=("Arial", 12),
            bg="lightgreen",
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="HỦY",
            command=edit_window.destroy,
            font=("Arial", 12),
            bg="lightgray",
            width=15
        ).pack(side=tk.LEFT, padx=5)

    def delete_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn khách hàng để xóa!")
            return

        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa khách hàng này?"):
            for item in selected:
                cust_index = self.tree.index(item)
                self.customer_data.pop(cust_index)
            self.update_customer_list()
            self.update_address_filter()
            self.save_data()
            self.clear_fields()
            messagebox.showinfo("Thành công", "Đã xóa khách hàng!")

    def search_customers(self, event=None):
        search_text = self.search_entry.get().lower()
        filtered_data = []
        
        for cust in self.customer_data:
            if (search_text in str(cust[1]).lower() or  # Mã KH
                search_text in str(cust[2]).lower() or   # Tên KH
                search_text in str(cust[3]).lower() or   # SĐT
                search_text in str(cust[5]).lower()):    # CCCD
                filtered_data.append(cust)
                
        self.update_customer_list(filtered_data)

    def filter_customers(self, event=None):
        selected_address = self.address_filter.get()
        if selected_address == "Tất cả":
            self.update_customer_list()
        else:
            filtered_data = [cust for cust in self.customer_data if cust[4] == selected_address]
            self.update_customer_list(filtered_data)

    def save_data(self):
        try:
            os.makedirs('data', exist_ok=True)
            data_to_save = []
            for cust in self.customer_data:
                cust_dict = {
                    "stt": cust[0],
                    "id": cust[1],
                    "name": cust[2],
                    "phone": cust[3],
                    "address": cust[4],
                    "id_card": cust[5]
                }
                data_to_save.append(cust_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {str(e)}")

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.customer_data = [
                        (
                            cust["stt"],
                            cust["id"],
                            cust["name"],
                            cust["phone"],
                            cust["address"],
                            cust["id_card"]
                        )
                        for cust in data
                    ]
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu: {str(e)}")

    def update_address_filter(self):
        addresses = ["Tất cả"] + list(set(cust[4] for cust in self.customer_data))
        self.address_filter['values'] = addresses

    def update_customer_list(self, data=None):
        self.tree.delete(*self.tree.get_children())
        data = data if data else self.customer_data
        for cust in data:
            self.tree.insert("", tk.END, values=cust)

    def clear_fields(self):
        self.customer_id_entry.delete(0, tk.END)
        self.customer_name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.id_card_entry.delete(0, tk.END)
class Invoice_Management(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.invoice_data = []
        self.data_file = "data/invoices.json"
        self.load_data()
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self, text="QUẢN LÝ HÓA ĐƠN", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Search Frame
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Tìm kiếm:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(search_frame, text="Lọc theo ngày:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.date_filter = ttk.Combobox(search_frame, values=["Tất cả"], font=("Arial", 12))
        self.date_filter.pack(side=tk.LEFT)
        self.date_filter.set("Tất cả")

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="XEM CHI TIẾT", font=("Arial", 12), 
                 command=self.show_invoice_details,
                 bg="lightblue", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="IN HÓA ĐƠN", font=("Arial", 12), 
                 command=self.print_invoice,
                 bg="lightgreen", width=15).pack(side=tk.LEFT, padx=10)
        
        # Invoice list
        list_frame = tk.LabelFrame(self, text="Danh Sách Hóa Đơn", padx=10, pady=0, font=("Arial", 12))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create Treeview with scrollbar
        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("STT", "Mã HĐ", "Số Phòng", "Ngày Nhận", "Ngày Trả", "Số Ngày", "Tổng Tiền", "Trạng Thái"),
            show="headings",
            height=10,
        )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        column_widths = {
            "STT": 50, 
            "Mã HĐ": 120,
            "Số Phòng": 80,
            "Ngày Nhận": 100,
            "Ngày Trả": 100,
            "Số Ngày": 80,
            "Tổng Tiền": 120,
            "Trạng Thái": 100
        }
        
        for col, width in column_widths.items():
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=width)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.search_entry.bind('<KeyRelease>', self.search_invoices)
        self.date_filter.bind('<<ComboboxSelected>>', self.filter_invoices)
        self.tree.bind('<Double-1>', lambda e: self.show_invoice_details())

        # Load initial data
        self.update_invoice_list()
        self.update_date_filter()

    def show_invoice_details(self):
        """Hiển thị chi tiết hóa đơn"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hóa đơn để xem chi tiết!")
            return

        idx = self.tree.index(selected[0])
        invoice = self.invoice_data[idx]

        details = f"""
CHI TIẾT HÓA ĐƠN

Mã hóa đơn: {invoice['invoice_id']}
Số phòng: {invoice['room_number']}
Loại phòng: {invoice['room_type']}

Ngày nhận phòng: {invoice['check_in']}
Ngày trả phòng: {invoice['check_out']}
Số ngày ở: {invoice['days']}

Giá phòng/ngày: {invoice['price_per_day']:,.0f} VNĐ
Tiền đặt cọc: {invoice['deposit']:,.0f} VNĐ
Tổng tiền: {invoice['total']:,.0f} VNĐ

Ngày thanh toán: {invoice['payment_date']}
Trạng thái: {invoice['status']}
"""
        messagebox.showinfo("Chi tiết hóa đơn", details)

    def search_invoices(self, event=None):
        """Tìm kiếm hóa đơn"""
        search_text = self.search_entry.get().lower()
        filtered_data = []
        
        for inv in self.invoice_data:
            if (search_text in inv['invoice_id'].lower() or
                search_text in inv['room_number'].lower() or
                search_text in inv['check_in'].lower()):
                filtered_data.append(inv)
                
        self.update_invoice_list(filtered_data)

    def filter_invoices(self, event=None):
        """Lọc hóa đơn theo ngày"""
        selected_date = self.date_filter.get()
        if selected_date == "Tất cả":
            self.update_invoice_list()
        else:
            filtered_data = [inv for inv in self.invoice_data if inv['check_in'] == selected_date]
            self.update_invoice_list(filtered_data)

    def update_date_filter(self):
        """Cập nhật danh sách ngày trong combobox"""
        dates = ["Tất cả"] + sorted(list(set(inv['check_in'] for inv in self.invoice_data)))
        self.date_filter['values'] = dates

    def update_invoice_list(self, data=None):
        """Cập nhật danh sách hóa đơn"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        display_data = data if data is not None else self.invoice_data
        for i, inv in enumerate(display_data, 1):
            self.tree.insert('', 'end', values=(
                i,
                inv['invoice_id'],
                inv['room_number'],
                inv['check_in'],
                inv['check_out'],
                inv['days'],
                f"{inv['total']:,.0f}",
                inv['status']
            ))
            
    def save_invoice_to_file(self, invoice, content):
        """In hóa đơn ra file"""
        try:
            os.makedirs('invoices', exist_ok=True)
            filename = f"invoices/hoa_don_{invoice['invoice_id']}_{invoice['payment_date'].replace('/', '_')}.txt"
        
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Thành công", f"Đã in hóa đơn ra file {filename}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể in hóa đơn: {str(e)}")

    def search_invoices(self, event=None):
        """Tìm kiếm hóa đơn"""
        search_text = self.search_entry.get().lower()
        filtered_data = []
    
        for inv in self.invoice_data:
            if (search_text in inv['invoice_id'].lower() or
                search_text in inv['room_number'].lower() or
                search_text in inv['check_in'].lower() or
                search_text in str(inv['total']).lower()):
                filtered_data.append(inv)
            
        self.update_invoice_list(filtered_data)

    def filter_invoices(self, event=None):
        """Lọc hóa đơn theo ngày"""
        selected_date = self.date_filter.get()
        if selected_date == "Tất cả":
            self.update_invoice_list()
        else:
            filtered_data = [inv for inv in self.invoice_data if inv['check_in'] == selected_date]
            self.update_invoice_list(filtered_data)

    def update_date_filter(self):
        """Cập nhật danh sách ngày trong combobox"""
        dates = ["Tất cả"] + sorted(list(set(inv['check_in'] for inv in self.invoice_data)))
        self.date_filter['values'] = dates

    def update_invoice_list(self, data=None):
        """Cập nhật danh sách hóa đơn"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        display_data = data if data is not None else self.invoice_data
        for i, inv in enumerate(display_data, 1):
            self.tree.insert('', 'end', values=(
                i,
                inv['invoice_id'],
                inv['room_number'],
                inv['check_in'],
                inv['check_out'],
                inv['days'],
                f"{inv['total']:,.0f}",
                inv['status']
            ))

    def load_data(self):
        """Đọc dữ liệu hóa đơn từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.invoice_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu hóa đơn: {str(e)}")

    def print_invoice(self):
        """In hóa đơn"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hóa đơn để in!")
            return

        idx = self.tree.index(selected[0])
        invoice = self.invoice_data[idx]

        # Tạo nội dung hóa đơn chi tiết
        content = f"""
        HÓA ĐƠN THANH TOÁN
        ------------------
    
        Mã hóa đơn: {invoice['invoice_id']}
        Số phòng: {invoice['room_number']}
        Loại phòng: {invoice['room_type']}
    
        Ngày nhận phòng: {invoice['check_in']}
        Ngày trả phòng: {invoice['check_out']}
        Số ngày ở: {invoice['days']}
    
        Giá phòng/ngày: {invoice['price_per_day']:,.0f} VNĐ
        Tiền đặt cọc: {invoice['deposit']:,.0f} VNĐ
        Tổng tiền: {invoice['total']:,.0f} VNĐ
    
        Ngày thanh toán: {invoice['payment_date']}
        Trạng thái: {invoice['status']}
        """

        # Hiển thị cửa sổ xem trước hóa đơn
        preview_window = tk.Toplevel(self)
        preview_window.title(f"Hóa đơn - {invoice['invoice_id']}")
        preview_window.geometry("400x600")

        text_widget = tk.Text(preview_window, font=("Courier", 12))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert(tk.END, content)
        text_widget.config(state='disabled')

        # Nút in và đóng
        button_frame = tk.Frame(preview_window)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="IN",
            command=lambda: self.save_invoice_to_file(invoice, content),
            font=("Arial", 12),
            bg="lightgreen",
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="ĐÓNG",
            command=preview_window.destroy,
            font=("Arial", 12),
            bg="lightgray",
            width=15
        ).pack(side=tk.LEFT, padx=5)    

        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Quản Lý Khách Sạn")
    app = ManagementApp(root)
    root.mainloop()

