import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSlider, QSpinBox, QGroupBox,
    QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class SerialThread(QThread):
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = True

    def run(self):
        try:
            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            import time
            time.sleep(0.5)
            time.sleep(0.5)
            self.connection_status.emit(True)
            self.data_received.emit(f"Connected to {self.port}")

            while self.running:
                try:
                    if self.serial.in_waiting > 0:
                        data = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            self.data_received.emit(f"Received: {data}")
                except Exception as e:
                    self.data_received.emit(f"Read error: {str(e)}")

                time.sleep(0.1)

        except Exception as e:
            self.connection_status.emit(False)
            self.data_received.emit(f"Connection error: {str(e)}")
            return

    def send_command(self, cmd):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(cmd.encode() + b'\r')
                self.serial.flush()
                self.data_received.emit(f"Sent: {cmd}")
            except Exception as e:
                self.data_received.emit(f"Send error: {str(e)}")
        else:
            self.data_received.emit("Error: Serial port not open")

    def stop(self):
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()


class PWMControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.init_ui()
        self.setWindowTitle("PWM Controller")
        self.setGeometry(100, 100, 600, 500)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Serial Port Section
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("COM Port:"))
        self.port_combo = QComboBox()
        self.update_ports()
        port_layout.addWidget(self.port_combo)

        port_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "9600", "19200", "38400", "57600"])
        self.baud_combo.setCurrentText("115200")
        port_layout.addWidget(self.baud_combo)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        port_layout.addWidget(self.connect_btn)

        main_layout.addLayout(port_layout)

        # Status Label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        main_layout.addWidget(self.status_label)

        # Channel 1 (PIN17)
        ch1_group = QGroupBox("Channel 1 (PIN17)")
        ch1_layout = QVBoxLayout()

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency (Hz):"))
        self.freq1_spinbox = QSpinBox()
        self.freq1_spinbox.setMinimum(1)
        self.freq1_spinbox.setMaximum(100000)
        self.freq1_spinbox.setValue(150)
        freq_layout.addWidget(self.freq1_spinbox)
        freq_layout.addStretch()
        ch1_layout.addLayout(freq_layout)

        dc_layout = QHBoxLayout()
        dc_layout.addWidget(QLabel("Duty Cycle (0-100%):"))
        self.dc1_slider = QSlider(Qt.Orientation.Horizontal)
        self.dc1_slider.setMinimum(0)
        self.dc1_slider.setMaximum(100)
        self.dc1_slider.setValue(0)
        self.dc1_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.dc1_slider.setTickInterval(10)
        dc_layout.addWidget(self.dc1_slider)
        self.dc1_label = QLabel("0%")
        self.dc1_label.setMinimumWidth(40)
        dc_layout.addWidget(self.dc1_label)
        self.dc1_slider.valueChanged.connect(self.update_dc1_label)
        ch1_layout.addLayout(dc_layout)

        ch1_group.setLayout(ch1_layout)
        main_layout.addWidget(ch1_group)

        # Channel 2 (PIN16)
        ch2_group = QGroupBox("Channel 2 (PIN14)")
        ch2_layout = QVBoxLayout()

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency (Hz):"))
        self.freq2_spinbox = QSpinBox()
        self.freq2_spinbox.setMinimum(1)
        self.freq2_spinbox.setMaximum(100000)
        self.freq2_spinbox.setValue(150)
        freq_layout.addWidget(self.freq2_spinbox)
        freq_layout.addStretch()
        ch2_layout.addLayout(freq_layout)

        dc_layout = QHBoxLayout()
        dc_layout.addWidget(QLabel("Duty Cycle (0-100%):"))
        self.dc2_slider = QSlider(Qt.Orientation.Horizontal)
        self.dc2_slider.setMinimum(0)
        self.dc2_slider.setMaximum(100)
        self.dc2_slider.setValue(0)
        self.dc2_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.dc2_slider.setTickInterval(10)
        dc_layout.addWidget(self.dc2_slider)
        self.dc2_label = QLabel("0%")
        self.dc2_label.setMinimumWidth(40)
        dc_layout.addWidget(self.dc2_label)
        self.dc2_slider.valueChanged.connect(self.update_dc2_label)
        ch2_layout.addLayout(dc_layout)

        ch2_group.setLayout(ch2_layout)
        main_layout.addWidget(ch2_group)

        # Apply Button
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.apply_btn.setStyleSheet("padding: 10px; background-color: #4CAF50; color: white;")
        self.apply_btn.clicked.connect(self.apply_settings)
        self.apply_btn.setEnabled(False)
        main_layout.addWidget(self.apply_btn)

        # Log/Status area
        from PyQt6.QtWidgets import QTextEdit
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("border: 1px solid gray; padding: 5px; font-family: monospace; font-size: 9px;")
        main_layout.addWidget(QLabel("Response Log:"))
        main_layout.addWidget(self.log_text)

        central_widget.setLayout(main_layout)

    def update_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        if port_list:
            self.port_combo.addItems(port_list)
        else:
            self.port_combo.addItem("No ports available")

    def toggle_connection(self):
        if self.serial_thread is None or not self.serial_thread.isRunning():
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        port_info = self.port_combo.currentText()
        if "No ports available" in port_info:
            QMessageBox.warning(self, "Error", "No COM ports available")
            return

        port = port_info.split(" - ")[0]
        baudrate = int(self.baud_combo.currentText())

        self.serial_thread = SerialThread(port, baudrate)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.data_received.connect(self.on_data_received)
        self.serial_thread.start()

    def disconnect(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setText("Connect")
        self.apply_btn.setEnabled(False)

    def on_connection_status(self, connected):
        if connected:
            self.status_label.setText(f"Connected to {self.port_combo.currentText()}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.apply_btn.setEnabled(True)
            self.log_text.clear()
            self.log_text.append("Connected successfully. Ready to send commands.")
        else:
            self.status_label.setText("Connection Failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.apply_btn.setEnabled(False)

    def on_data_received(self, data):
        self.log_text.append(data)

    def update_dc1_label(self):
        self.dc1_label.setText(f"{self.dc1_slider.value()}%")

    def update_dc2_label(self):
        self.dc2_label.setText(f"{self.dc2_slider.value()}%")

    def apply_settings(self):
        if not self.serial_thread or not self.serial_thread.isRunning() or not self.serial_thread.serial:
            QMessageBox.warning(self, "Error", "Not connected to device. Please connect first.")
            return

        freq1 = self.freq1_spinbox.value()
        dc1 = self.dc1_slider.value()
        freq2 = self.freq2_spinbox.value()
        dc2 = self.dc2_slider.value()

        self.log_text.clear()
        cmd = f"SET=3,{freq1},{dc1},{freq2},{dc2}"
        self.serial_thread.send_command(cmd)

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    gui = PWMControlGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
