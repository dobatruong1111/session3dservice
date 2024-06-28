package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.config.ConfigProperties;
import com.saolasoft.websocket.config.model.ResourceProperty;
import com.saolasoft.websocket.session3d.model.Resource3d;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@Component
public class ResourceManager {
	
	private Map<String, Resource3d> resources;
	
	public ResourceManager(ConfigProperties configProperties) {
		this.resources = new HashMap<>();

		for (ResourceProperty resourceProperty : configProperties.getResources()) {
			String host = resourceProperty.getHost();
			List<Integer> portList = IntStream.rangeClosed(resourceProperty.getPortRange().get(0),
					resourceProperty.getPortRange().get(1))
					.boxed().collect(Collectors.toList());

			if (!resources.containsKey(host)) {
				resources.put(host, new Resource3d(portList, new ArrayList<>()));
			} else {
				resources.get(host).getAvailable().addAll(portList);
			}
		}
	}

	public String getNextResource() {
		String winner = null;
		int availibilityCount = 0;
		
		for (String host: this.resources.keySet()) {
			if (availibilityCount < this.resources.get(host).getAvailable().size()) {
				availibilityCount = this.resources.get(host).getAvailable().size();
				winner = host;
			}
		}
		
		if (winner != null) {
			int size = this.resources.get(winner).getAvailable().size();
			int port = this.resources.get(winner).getAvailable().get(size - 1);
			this.resources.get(winner).getAvailable().remove(size - 1);
			this.resources.get(winner).getUsed().add(port);
			return String.format("%s:%d", winner, port);
		}
		return "";
	}
	
	public void freeResource(String host, int port) {
		if (this.resources.containsKey(host)) {
			if (this.resources.get(host).getUsed().contains(port)) {
				int index = this.resources.get(host).getUsed().indexOf(port);
				this.resources.get(host).getUsed().remove(index);
			}
			if (!this.resources.get(host).getAvailable().contains(port)) {
				this.resources.get(host).getAvailable().add(port);
			}
		}
	}
}
