def removezero_ip(ip):
	return str.join('.', (str(int(part)) for part in ip.split('.')))
