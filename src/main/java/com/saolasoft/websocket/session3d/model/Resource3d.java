package com.saolasoft.websocket.session3d.model;

import java.util.List;

public class Resource3d {
	
	private List<Integer> available;
	private List<Integer> used;
	
	public Resource3d(List<Integer> available, List<Integer> used) {
		this.available = available;
		this.used = used;
	}
	
	public List<Integer> getAvailableResource() {
		return this.available;
	}
	
	public List<Integer> getUsedAvailable() {
		return this.used;
	}
}
