#!/usr/bin/python

import json, cgi, os, time, sys, subprocess, re, glob, atexit, datetime, socket

state_dir = '/var/www/.run/'
kill_bin = '/usr/bin/killall'
dump_name = 'dump'

"""
FIXME: tcpdump must be owned by HTTP server user's group and suid root, e.g.:
-rwsr-s--- 1 root www-data 1023160 Apr 24  2015 /var/www/.bin/tcpdump
"""
tcpdump_bin = '/var/www/.bin/tcpdump'

print 'Content-Type: application/json'
print

def become_daemon():
	pid = os.fork()
	if pid > 0:
		""" Return to parent """
		return False
	os.setsid()
	pid = os.fork()
	if pid > 0:
		os._exit(0)
	fd = os.open(os.devnull, os.O_RDWR)
	os.dup2(fd, sys.stdin.fileno())
	os.dup2(fd, sys.stdout.fileno())
	os.dup2(fd, sys.stderr.fileno())
	""" Return to child """
	return True

def dump_running():
	filename = state_dir + '/' + dump_name + '.pid'
	try:
		f = open(filename, 'r')
		pid = int(f.read())
		f.close()
		os.kill(pid, 0)
		return True
	except:
		return False

def parse_line(line):
	p = re.compile("^IP (.*) >")
	m = p.search(line)
	ping_src = m.group(1)

	p = re.compile("id ([0-9]+)")
	m = p.search(line)
	ping_id = m.group(1)

	p = re.compile("seq ([0-9]+)")
	m = p.search(line)
	ping_seq = m.group(1)

	return { 'ping_src' : ping_src, 'ping_id' : ping_id, 'ping_seq' : ping_seq }

def cleanup_dump():
	os.remove(state_dir + '/' + dump_name + '.pid')
	pings = glob.glob(state_dir + '/' + dump_name + '.*.json')
	for p in pings:
		os.remove(p)

def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 53))
	ip_addr = s.getsockname()[0]
	return ip_addr

def take_a_dump():
	if become_daemon():
		""" Parent, start dump """
		f = open(state_dir + '/' + dump_name + '.pid', 'w')
		f.write(str(os.getpid()))
		f.close()
		atexit.register(cleanup_dump)

		devnull = open(os.devnull, 'w')
		filter_arg = 'icmp[0] == 8 and dst ' + get_ip_address()
		p = subprocess.Popen([tcpdump_bin, '-ntl', '-i', 'eth0', filter_arg], stdout=subprocess.PIPE, stderr=devnull)

		while True:
			line = p.stdout.readline()
			if line == '' and p.poll() is not None:
				break
			if line:
				ping = parse_line(line)
				"""f = open(state_dir + '/' + dump_name + '.' + ping['ping_id'] + '.json', 'w')"""
				f = open(state_dir + '/' + dump_name + '.' + ping['ping_src'] + '.json', 'w')
				f.write(json.dumps(ping))
				f.close()
		f = open(state_dir + '/' + dump_name + '.pid.fail', 'w')
		f.write(str(p.wait()))
                f.close()
		os._exit(0)
	else:
		""" Child """
		return

if not dump_running():
	take_a_dump()

filenames = glob.glob(state_dir + '/' + dump_name + '.*.json')
i = 0
response = { }
for fn in filenames:
	mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(fn))
	if datetime.datetime.now() - mod_time > datetime.timedelta(seconds=2):
		""" Remove stale ping """
		os.remove(fn)
		continue
	f = open(fn)
	ping = json.load(f)
	response[ping['ping_id']] = ping
	f.close()
print json.dumps(response)
