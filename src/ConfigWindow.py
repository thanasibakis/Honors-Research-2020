from PySide2 import QtGui, QtWidgets
import serial.tools.list_ports

import config
from streams import SimulatedStream, SerialStream, UDPStream


WINDOW_TITLE = "MUGIC Config"


class ConfigWindow(QtWidgets.QWidget):
    def get_stream(self):
        stream_type = self.get_stream_type()

        if stream_type == "Simulated":
            stream = SimulatedStream(delay_ms=5)

        elif stream_type == "USB":
            port = self.get_serial_port()

            if not port:
                return None

            baud = self.get_serial_baud()

            if not baud:
                return None

            stream = SerialStream(port, baud)

        elif stream_type == "WiFi":
            ip = self.get_udp_ip()

            if ip is None:
                return None

            port = self.get_udp_port()

            if not port:
                return None

            stream = UDPStream(ip, port)
        
        else:
            return None

        return stream


    def get_stream_type(self):
        stream_types = ("Simulated", "USB", "WiFi")
		
        stream_type, ok = QtGui.QInputDialog.getItem(
            self, WINDOW_TITLE, "Sensor connection type?", stream_types, 2, False
        )
			
        return stream_type if ok else None


    def get_serial_port(self):
        available_ports = [port.device for port in serial.tools.list_ports.comports()]

        port, ok = QtGui.QInputDialog.getItem(
            self, WINDOW_TITLE, "Serial port?", available_ports, 0, False
        )
			
        return port if ok else None

    def get_serial_baud(self):
        port, ok = QtGui.QInputDialog.getText(
            self, WINDOW_TITLE, "Baud?", QtGui.QLineEdit.Normal, str(config.BAUD)
        )
			
        return port if ok else None

    def get_udp_ip(self):
        ip, ok = QtGui.QInputDialog.getText(
            self, WINDOW_TITLE, "Sensor UDP IP address?", QtGui.QLineEdit.Normal, config.IP
        )
			
        return ip if ok else None

    def get_udp_port(self):
        port, ok = QtGui.QInputDialog.getText(
            self, WINDOW_TITLE, "Sensor UDP port?", QtGui.QLineEdit.Normal, str(config.UDP_PORT)
        )
			
        return port if ok else None