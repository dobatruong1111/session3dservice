package com.saolasoft.websocket.config.model;

import java.util.List;

public class ResourceProperty {
	
	private String host;
	private List<Integer> portRange;
	
	public String getHost() {
		return this.host;
	}
	
	public List<Integer> getPortRange() {
		return this.portRange;
	}
	
	public void setHost(String host) {
		this.host = host;
	}
	
	public void setPortRange(List<Integer> portRange) {
		this.portRange = portRange;
	}
}
