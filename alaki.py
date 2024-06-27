#
# 
#

import tkinter as tk
from tkinter import ttk, messagebox
import re

def validate_ip(ip):
    """ Validate if the string is a valid IP address. """
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
        return True
    return False

def validate_input(*args):
    """ Validate the input fields. """
    ipv4_1 = ipv4_entry_1.get()
    ipv4_2 = ipv4_entry_2.get()
    ipv6_1 = ipv6_entry_1.get()
    ipv6_2 = ipv6_entry_2.get()

    ip_addresses = [ipv4_1, ipv4_2, ipv6_1, ipv6_2]
    valid_ips = [ip for ip in ip_addresses if ip and validate_ip(ip)]

    if not valid_ips:
        return False
    return True

# Create the main window
root = tk.Tk()
root.title("DNS Server Input")

# Create and place the DNS server name entry
ttk.Label(root, text="DNS Server Name:").grid(column=0, row=0, padx=10, pady=10)
dns_entry = ttk.Entry(root)
dns_entry.grid(column=1, row=0, padx=10, pady=10)

# Create and place the IPv4 entry fields
ttk.Label(root, text="IPv4 Address 1:").grid(column=0, row=1, padx=10, pady=10)
ipv4_entry_1 = ttk.Entry(root, validate='key', validatecommand=(root.register(validate_input), '%P'))
ipv4_entry_1.grid(column=1, row=1, padx=10, pady=10)

ttk.Label(root, text="IPv4 Address 2:").grid(column=0, row=2, padx=10, pady=10)
ipv4_entry_2 = ttk.Entry(root, validate='key', validatecommand=(root.register(validate_input), '%P'))
ipv4_entry_2.grid(column=1, row=2, padx=10, pady=10)

# Create and place the IPv6 entry fields
ttk.Label(root, text="IPv6 Address 1:").grid(column=0, row=3, padx=10, pady=10)
ipv6_entry_1 = ttk.Entry(root, validate='key', validatecommand=(root.register(validate_input), '%P'))
ipv6_entry_1.grid(column=1, row=3, padx=10, pady=10)

ttk.Label(root, text="IPv6 Address 2:").grid(column=0, row=4, padx=10, pady=10)
ipv6_entry_2 = ttk.Entry(root, validate='key', validatecommand=(root.register(validate_input), '%P'))
ipv6_entry_2.grid(column=1, row=4, padx=10, pady=10)

# Create and place the validate button
validate_button = ttk.Button(root, text="Validate", command=lambda: messagebox.showinfo("Validation", "Input is valid." if validate_input() else "At least one valid IP address must be provided."))
validate_button.grid(column=0, row=5, columnspan=2, pady=20)

# Start the GUI event loop
root.mainloop()


def main() -> None:
    setDnsDhcp('Ethernet 3')


if __name__ == '__main__':
    main()
