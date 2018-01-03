var snd = new Audio('ping.mp3');

var ping_srcs = [];
var timer = null;

function do_ping() {
	$('#ping_anim').attr('src', 'ping_anim.gif');
	snd.play();
}

function stop_ping() {
	clearInterval(timer);
	timer = null;
	$('#ping_static').show();
	$('#ping_anim').hide();
}

function start_ping() {
	$('#ping_anim').show();
	$('#ping_static').hide();
	timer = setInterval(show_pings, 1000);
}

function show_pings() {
	$('#content').hide();
	$('#content').empty();
	if (ping_srcs.length == 0) {
		stop_ping();
		return;
	} else {
		if (!timer) {
			start_ping();
		}
	}
	for (i = 0; i < ping_srcs.length; i++) {
		ping_src = ping_srcs[i];
		$('#content').append('<div id="ip">' + ping_src + '</div>');
	}
	$('#content').fadeIn("fast");
	do_ping();
}

function poll_pings() {
	$.getJSON("/cgi-bin/pong.py", function(result) {
		ping_srcs.length = 0;
		$.each(result, function(ping_id, ping) {
			ping_srcs.push(ping['ping_src']);
		});
		if (ping_srcs.length > 0 && !timer) {
			show_pings();
		}
	});
}

function show_link() {
	var link = document.createElement('a');
	var str = 'Ping me';
	link.setAttribute('href', 'http://ping.eu/ping/?host=' + location.host);
	link.setAttribute('target', '_blank');
	link.setAttribute('title', str);
	link.appendChild(document.createTextNode(str));
	$('#header').fadeTo(0, 0);
	$('#header').css("animation", "none");
	$('#header').empty();
	$('#header').append(link);
 	$('#header').append(' at ' + location.host);
	$('#header').fadeTo("fast", 1);
}
