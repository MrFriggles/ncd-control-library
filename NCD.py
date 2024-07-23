"""NCD ethernet library."""

import enum
import os
import socket
import subprocess


def calculatechecksum(msg):
    """

    :param msg:
    :return:
    """
    chksum = 0
    for b in msg:
        chksum += int.from_bytes(b)
    return chksum & 0xff


class NCDDevice:
    """Class to control NCD ethernet devices."""

    sock = None
    port = None
    ip = ""
    tx_msglen = 6
    rx_msglen = 4
    max_relays_per_bank = 8
    max_banks = 32
    ncd_message_soh = b"\xAA"
    ncd_command_hdr = b"\xFE"
    ncd_base_off_command = 0x63
    ncd_base_on_command = ncd_base_off_command + max_relays_per_bank
    ncd_base_chksum = 0x0E
    ncd_mac_oui = "00-08-dc"

    ALL_BANKS = 0

    class Relays(enum):
        RELAY_1 = 1
        RELAY_2 = 2
        RELAY_3 = 3
        RELAY_4 = 4
        RELAY_5 = 5
        RELAY_6 = 6
        RELAY_7 = 7
        RELAY_8 = 8

    def __init__(self, port, ip=None):
        """Create an NCDDevice object with a port and optional IP address.

        :param port: The TCP network port the NCD device is
                     listening for connections.
        :param ip: Optional parameter. Set the IP address if known.
         Otherwise, try to find it on the network
        """
        if ip is None:
            self.__findip()
        else:
            self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __findip(self):
        """Attempts to find an NCD device on the network.
        Note! That this will use the first device it has found.

        :return None
        """
        try:
            if os.name == 'nt':
                # https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/arp
                self.ip = str(subprocess.check_output(
                    f"arp -a | findstr \"{self.ncd_mac_oui}\" ",
                    shell=True,
                    stderr=subprocess.STDOUT)).split(' ')[2]
                socket.inet_aton(self.ip)
            else:
                # https://man7.org/linux/man-pages/man8/arp.8.html
                # TODO: Test me!
                self.ip = str(subprocess.check_output(
                    f"arp | grep \"{self.ncd_mac_oui}\" ",
                    shell=True,
                    stderr=subprocess.STDOUT)).split(' ')[0]

            print(f"Found NCD device on network with IP: {self.ip}")
        except (OSError, IndexError):
            print("Unable to find an NCD device on network. Run the NCDConfig"
                  " tool to troubleshoot connection issues")
            self.ip = ""

    def __receive(self):
        """Reads in a message of length RCDDevice.rx_msglen from the
        connected NCD device. Usually in response from a send() call.

        Throws RuntimeError

        :return bytestring
        """
        rx_data = []
        bytes_rxd = 0
        while bytes_rxd < self.rx_msglen:
            chunk = self.sock.recv(self.rx_msglen - bytes_rxd)
            if chunk == b'':
                raise RuntimeError("socket connection broken."
                                   " Failed to read socket.")
            rx_data.append(chunk)
            bytes_rxd = bytes_rxd + len(chunk)
        return b''.join(rx_data)

    def __send(self, data):
        """Sends a message of length RCDDevice.tx_msglen to the
        connected NCD device. Call receive() after to read response.

        :param data: The message to send and control the NCD device.
        :return: None
        """
        # TODO: Need to validate data and length
        total_sent = 0
        while total_sent < self.tx_msglen:
            sent = self.sock.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken."
                                   " Failed to send to socket.")
            total_sent = total_sent + sent

    def __switchonrelay(self, bank, relay):
        """

        :param bank:
        :param relay:
        :return:
        """
        relay_command = self.ncd_message_soh \
            + b"\x03" \
            + self.ncd_command_hdr \
            + (self.ncd_base_on_command + relay).to_bytes() \
            + bank.to_bytes()
        relay_command += calculatechecksum(relay_command).to_bytes()
        self.__send(relay_command)

    def __switchoffrelay(self, bank, relay):
        """

        :param bank:
        :param relay:
        :return:
        """
        relay_command = self.ncd_message_soh \
            + b"\x03" \
            + self.ncd_command_hdr \
            + (self.ncd_base_off_command + relay).to_bytes() \
            + bank.to_bytes()
        relay_command += calculatechecksum(relay_command).to_bytes()
        self.__send(relay_command)

    def connect(self):
        """Connects to the IP and port provided from initialization.

        :return None
        """
        # TODO: Check if connect() succeeded here
        self.sock.connect((self.ip, self.port))

    def switchrelay(self, bank, relay, on=True):
        """

        :param bank:
        :param relay:
        :param on:
        :return:
        """
        if bank < 0 or bank > self.max_banks:
            raise RuntimeWarning("invalid bank address")
        if relay < 1 or relay > self.max_relays_per_bank:
            raise RuntimeWarning("invalid relay address")

        if on:
            self.__switchonrelay(bank, relay)
        else:
            self.__switchoffrelay(bank, relay)
