package com.saolasoft.websocket.config.model;

import java.util.List;

public class ViewerProperty {

	private List<String> cmd;
	private String readyLine;
	
	public List<String> getCmd() {
		return this.cmd;
	}
	
	public String getReadyLine() {
		return this.readyLine;
	}
	
	public void setCmd(List<String> cmd) {
		this.cmd = cmd;
	}
	
	public void setReadyLine(String readyLine) {
		this.readyLine = readyLine;
	}
}
