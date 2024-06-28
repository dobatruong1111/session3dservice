package com.saolasoft.websocket.session3d.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class Session3d {
	
	private String id;

	private String host;

	private int port;

	private String websocketUrl;

	private String cmd;
}
