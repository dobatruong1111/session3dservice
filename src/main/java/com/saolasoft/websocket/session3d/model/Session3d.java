package com.saolasoft.websocket.session3d.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class Session3d {
	
	private String id;

	private String host;

	private int port;

	private String sessionUrl;

	private String cmd;
	
	public Session3d(String id, String host, int port, String sessionUrl, String cmd) {
		this.id = id;
		this.host = host;
		this.port = port;
		this.sessionUrl = sessionUrl;
		this.cmd = cmd;
	}
}
